
import os

# 1. Fix utils.py
print("Fixing utils.py...")
try:
    with open('utils.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
            
    # Find the end of the clean content
    marker = "return teams"
    idx = content.find(marker)
    
    if idx != -1:
        clean_content = content[:idx + len(marker)] + "\n\n"
        
        # Read the clean TeamBalancer code
        with open(r'C:\Users\rajve\Desktop\SkillIssues\TeamBalancer.py', 'r', encoding='utf-8') as f:
            new_code = f.read()
            
        with open('utils.py', 'w', encoding='utf-8') as f:
            f.write(clean_content + new_code)
        print("utils.py fixed.")
    else:
        print("Marker 'return teams' not found in utils.py")

except Exception as e:
    print(f"Error fixing utils.py: {e}")

# 2. Fix glasstry.py
print("Fixing glasstry.py...")
try:
    with open('glasstry.py', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
            
    # Find the end of the clean content
    marker = 'elif st.session_state.page == "view_folders": view_folders()'
    idx = content.find(marker)
    
    if idx != -1:
        clean_content = content[:idx + len(marker)] + "\n\n"
        
        # Read the clean TeamUI code
        with open(r'C:\Users\rajve\Desktop\SkillIssues\TeamUI.py', 'r', encoding='utf-8') as f:
            new_code = f.read()
            
        with open('glasstry.py', 'w', encoding='utf-8') as f:
            f.write(clean_content + new_code)
        print("glasstry.py fixed.")
    else:
        print("Marker not found in glasstry.py")

except Exception as e:
    print(f"Error fixing glasstry.py: {e}")
