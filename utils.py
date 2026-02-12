import random
import pandas as pd

class SeatingManager:
    def __init__(self, rows, cols, cluster_size=1):
        self.rows = rows
        self.cols = cols
        self.cluster_size = cluster_size
        self.row_labels = [chr(65+i) for i in range(rows)] # A, B, C...

    def allocate_seat(self, event_data, gender):
        """
        Allocates a seat based on gender clustering.
        Pattern: F F F | M M M | F F F ... (if cluster_size=3)
        Default start: Female.
        """
        # 1. Map occupied seats
        occupied = set()
        for p in event_data:
            if 'seat' in p and p['seat']:
                occupied.add(p['seat'])

        # 2. Iterate through all seats to find first available matching gender slot
        # Flattened index: 0 to (rows*cols - 1)
        total_seats = self.rows * self.cols
        
        for i in range(total_seats):
            r = i // self.cols
            c = i % self.cols
            
            # Determine Target Gender for this seat
            # Group index in the linear sequence
            group_idx = i // self.cluster_size
            
            # Pattern: Even groups -> Female, Odd -> Male (or vice versa)
            # Let's say 0=Female, 1=Male
            is_female_slot = (group_idx % 2 == 0)
            
            target = 'Female' if is_female_slot else 'Male'
            
            # Check match
            # "Non-Binary" can sit anywhere? Or specific?
            # User said: "no gender feels uncomfortable". 
            # Non-Binary might prefer Male or Female slots? 
            # Let's assign Non-Binary to Male slots for now as a fallback, or Any Empty?
            # Let's strict match for M/F, and allow NB in Male slots (arbitrary convention)
            
            match = False
            if gender == 'Female' and target == 'Female': match = True
            elif gender == 'Male' and target == 'Male': match = True
            elif gender == 'Non-Binary' and target == 'Male': match = True # Treat as Male for seating
            
            if match:
                seat_label = f"Row {self.row_labels[r]}, Seat {c + 1}"
                if seat_label not in occupied:
                    return seat_label
                    
        return "Event Full (for this gender)"

class TeamManager:
    @staticmethod
    def generate_teams(participants, team_size=4):
        """
        participants: list of dicts with 'gender', 'name'
        Returns: list of teams (lists of people)
        """
        # Separate by gender
        males = [p for p in participants if p['gender'] == 'Male']
        females = [p for p in participants if p['gender'] == 'Female']
        others = [p for p in participants if p['gender'] not in ['Male', 'Female']]
        
        # Shuffle
        random.shuffle(males)
        random.shuffle(females)
        random.shuffle(others)
        
        teams = []
        # Create balanced teams
        # Strategy: Distribute M/F equally
        
        all_people = males + females + others
        num_teams = (len(all_people) + team_size - 1) // team_size
        
        teams = [[] for _ in range(num_teams)]
        
        # Round robin distribution of each group to ensure balance
        for group in [males, females, others]:
            for i, p in enumerate(group):
                teams[i % num_teams].append(p)
                
        return teams


class TeamBalancer:
    """
    Manages team role allocation with gender balancing.
    """
    @staticmethod
    def calculate_score(candidate_skills, role_reqs):
        """
        candidate_skills: dict {skill: level(0-10)}
        role_reqs: dict {skill: weight(0-10)}
        Returns: float (0.0 to 1.0)
        """
        total_weight = sum(role_reqs.values())
        if total_weight == 0: return 0.0
        
        score_sum = 0
        
        # Check if candidate_skills is a list (binary) or dict (weighted - backward compat)
        is_binary = isinstance(candidate_skills, list) or isinstance(candidate_skills, set)
        
        for skill, weight in role_reqs.items():
            # Check presence
            has_skill = False
            
            if is_binary:
                # List/Set check (Case insensitive)
                for c_s in candidate_skills:
                    if c_s.lower() == skill.lower():
                        has_skill = True
                        break
                if has_skill:
                    score_sum += weight
            else:
                # Dict check (Old behavior: weighted proficiency)
                c_skill = 0
                for k, v in candidate_skills.items():
                    if k.lower() == skill.lower():
                        c_skill = v
                        break
                score_sum += c_skill * weight
            
        # Max Possible
        if is_binary:
            max_possible = total_weight
        else:
            max_possible = total_weight * 10
            
        if max_possible == 0: return 0.0
        
        return score_sum / max_possible

    @staticmethod
    def allocate_roles(candidates, roles, balance_threshold=0.0):
        """
        candidates: list of dict {id, name, gender, skills: {sk: lvl}}
        roles: dict {role_name: {reqs: {sk: w}, count: N}}
        balance_threshold: float (e.g. 0.20 for 20%)
        
        Returns: 
           assignments: {role_name: [candidate_obj, ...]}
           logs: list of strings (audit trail)
        """
        logs = []
        # 1. Calculate all scores
        # scores[role][candidate_id] = score
        scores = {}
        for r_name, r_data in roles.items():
            scores[r_name] = []
            for c in candidates:
                s = TeamBalancer.calculate_score(c['skills'], r_data['reqs'])
                scores[r_name].append({'c': c, 'score': s})
            # Sort by score desc
            scores[r_name].sort(key=lambda x: x['score'], reverse=True)

        # 2. Initial Allocation (Greedy by best score)
        # We need to respect role counts.
        assignments = {r: [] for r in roles}
        assigned_ids = set()
        
        # Flatten all possible assignments: (role, candidate, score)
        all_options = []
        for r_name, cand_list in scores.items():
            for item in cand_list:
                all_options.append({'r': r_name, 'c': item['c'], 's': item['score']})
        
        # Sort all options by score
        all_options.sort(key=lambda x: x['s'], reverse=True)
        
        # Allocate
        for opt in all_options:
            r = opt['r']
            c = opt['c']
            cid = c['id']
            
            if cid in assigned_ids: continue
            if len(assignments[r]) >= roles[r]['count']: continue
            
            assignments[r].append(opt)
            assigned_ids.add(cid)
            
        # 3. Balance Check & Swapping
        if balance_threshold > 0:
            logs.append(f"Starting Balance Check (Threshold: {balance_threshold})")
            
            # Helper to get gender counts
            def get_counts(role_list):
                m = len([x for x in role_list if x['c']['gender'] == 'Male'])
                f = len([x for x in role_list if x['c']['gender'] == 'Female'])
                return m, f

            # Max iterations to prevent infinite loops
            for _ in range(len(roles) * 2):
                made_change = False
                
                for r_name, assigned in assignments.items():
                    if not assigned: continue
                    
                    m, f = get_counts(assigned)
                    diff_count = m - f
                    
                    dominant = None
                    if diff_count >= 2: dominant = 'Male'   # e.g. 2M, 0F -> diff 2. 3M, 1F -> diff 2.
                    elif diff_count <= -2: dominant = 'Female'
                    
                    if dominant:
                        # Attempt to fix this role
                        target_gender = 'Female' if dominant == 'Male' else 'Male'
                        
                        # Candidates to remove (Dominant gender in this role), sorted by lowest score first
                        to_remove_candidates = [x for x in assigned if x['c']['gender'] == dominant]
                        to_remove_candidates.sort(key=lambda x: x['s'])
                        
                        if not to_remove_candidates: continue
                        cand_out = to_remove_candidates[0]
                        
                        # Find best swap IN
                        best_swap = None
                        swap_type = None # 'unassigned' or 'role_swap'
                        source_role = None
                        
                        # 1. Check Unassigned
                        unassigned_candidates = [c for c in candidates if c['id'] not in assigned_ids and c['gender'] == target_gender]
                        
                        for c in unassigned_candidates:
                            s = TeamBalancer.calculate_score(c['skills'], roles[r_name]['reqs'])
                            loss = cand_out['s'] - s
                            if loss <= balance_threshold:
                                # We want the best score possible
                                if best_swap is None or s > best_swap['s']:
                                    best_swap = {'c': c, 's': s, 'loss': loss}
                                    swap_type = 'unassigned'
                        
                        # 2. Check Inter-Role Swaps (only if unassigned didn't solve it optimally or at all)
                        # We look for a candidate in another role who is the Target Gender
                        # AND we must send our cand_out to that role? Or just swap?
                        # Let's try direct swap: A (from r1, dom) <-> B (from r2, target)
                        # Condition: 
                        # - r1 gets better balance (Yes, -1 Dom, +1 Target)
                        # - r2 balance check: Does receiving Dom hurt it? 
                        #     If r2 has excess Target, removing Target helps.
                        #     If r2 is balanced, receiving Dom might unbalance it.
                        #     We allow swap if r2 new balance is "okay" (diff < 2) OR if r2 was already bad in the other direction.
                        
                        if not best_swap: 
                            for r_other, assigned_other in assignments.items():
                                if r_other == r_name: continue
                                
                                m_other, f_other = get_counts(assigned_other)
                                # We want to take a 'target_gender' from r_other
                                # So r_other loses 'target_gender' and gains 'dominant' (from r_name)
                                
                                # Check if r_other can afford losing target_gender
                                # If target is Female: r_other loses F, gains M.
                                # New M = m_other + 1, New F = f_other - 1.
                                # New Diff = (m_other+1) - (f_other-1) = m_other - f_other + 2.
                                # We accept if abs(New Diff) < 2 OR abs(New Diff) < abs(Current Diff) (Correction)
                                
                                current_diff_other = m_other - f_other
                                change = 2 if dominant == 'Male' else -2 # If we send a Male, diff increases by 2
                                new_diff_other = current_diff_other + change
                                
                                if abs(new_diff_other) >= 2 and abs(new_diff_other) >= abs(current_diff_other):
                                    continue # This swap hurts the other role too much, skip
                                
                                # Find candidates in r_other of target_gender
                                candidates_in_other = [x for x in assigned_other if x['c']['gender'] == target_gender]
                                
                                for c_in in candidates_in_other:
                                    # Calculate scores for the swap
                                    # Score of c_in in New Role (r_name)
                                    s_new_r1 = TeamBalancer.calculate_score(c_in['c']['skills'], roles[r_name]['reqs'])
                                    # Score of cand_out in Other Role (r_other)
                                    s_new_r2 = TeamBalancer.calculate_score(cand_out['c']['skills'], roles[r_other]['reqs'])
                                    
                                    # Calculate logic checks
                                    # Loss in r_name
                                    loss_r1 = cand_out['s'] - s_new_r1
                                    # Loss in r_other
                                    # Find c_in's current score in r_other (it's stored in 's')
                                    # We need to find the object in assignments to be sure, or trust iteration
                                    # c_in is the object from assigned_other list, so c_in['s'] is correct
                                    loss_r2 = c_in['s'] - s_new_r2
                                    
                                    # Total Average Loss or Max Loss?
                                    # Let's say if BOTH losses are within threshold? Or Avg?
                                    # Let's use strict: Both must be acceptable drops? Or Sum?
                                    # Let's use Sum of loss <= threshold * 2 or similar.
                                    # To be safe: max(loss_r1, loss_r2) <= balance_threshold
                                    
                                    if loss_r1 <= balance_threshold and loss_r2 <= balance_threshold:
                                        # Found a valid swap!
                                        # We accept first valid logic or search for best? 
                                        # Let's take just valid for now to solve imbalance
                                        best_swap = {
                                            'type': 'role_swap',
                                            'r_other': r_other,
                                            'c_in': c_in,    # The person coming to r_name
                                            'c_out': cand_out, # The person leaving r_name
                                            's_new_r1': s_new_r1,
                                            's_new_r2': s_new_r2
                                        }
                                        swap_type = 'role_swap'
                                        source_role = r_other
                                        break
                                if best_swap: break
                        
                        # Execute Swap if found
                        if best_swap:
                            logs.append(f"Fixing imbalance in '{r_name}' ({dominant} dom). Target: {target_gender}")
                            
                            if swap_type == 'unassigned':
                                c_in = best_swap['c']
                                s_in = best_swap['s']
                                
                                logs.append(f"-> Swapped Unassigned: {cand_out['c']['name']} (out) <-> {c_in['name']} (in). Loss: {best_swap['loss']:.2f}")
                                
                                assignments[r_name].remove(cand_out)
                                assigned_ids.remove(cand_out['c']['id'])
                                
                                assignments[r_name].append({'r': r_name, 'c': c_in, 's': s_in})
                                assigned_ids.add(c_in['id'])
                                
                            elif swap_type == 'role_swap':
                                c_in_obj = best_swap['c_in'] # The full dict entry from other list
                                c_out_obj = best_swap['c_out']
                                r_other = best_swap['r_other']
                                
                                logs.append(f"-> Swapped with '{r_other}': {c_out_obj['c']['name']} (to {r_other}) <-> {c_in_obj['c']['name']} (to {r_name}).")
                                
                                # Update r_name list
                                assignments[r_name].remove(c_out_obj)
                                assignments[r_name].append({'r': r_name, 'c': c_in_obj['c'], 's': best_swap['s_new_r1']})
                                
                                # Update r_other list
                                assignments[r_other].remove(c_in_obj)
                                assignments[r_other].append({'r': r_other, 'c': c_out_obj['c'], 's': best_swap['s_new_r2']})
                                
                            made_change = True
                            break # Restart loop to re-evaluate all counts
                
                if not made_change:
                    break

        return assignments, logs
                        
        return assignments, logs
