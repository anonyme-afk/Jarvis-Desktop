import os
import sys

def inspect_jarvis_skills() -> str:
    """
    Inspects the JARVIS project directory, counts files, LOC, and active modules.
    Returns a formatted string report for the LLM.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    
    total_files = 0
    total_lines = 0
    ignored_dirs = {'venv', '__pycache__', '.git', 'node_modules', 'dist'}
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Exclude ignored directories
        dirnames[:] = [d for d in dirnames if d not in ignored_dirs]
        
        for file in filenames:
            if file.endswith('.py') or file.endswith('.js') or file.endswith('.ts') or file.endswith('.tsx'):
                total_files += 1
                filepath = os.path.join(dirpath, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        total_lines += sum(1 for _ in f)
                except Exception:
                    pass
                    
    # Check loaded modules (skills)
    loaded_skills = []
    for module_name in sys.modules.keys():
        if module_name.startswith('actions.') or module_name.startswith('core.') or module_name.startswith('memory.'):
            loaded_skills.append(module_name)
            
    report = (
        f"JARVIS Self-Inspection Report:\n"
        f"- Total Source Files (Python/TS/JS): {total_files}\n"
        f"- Total Lines of Code: {total_lines}\n"
        f"- Active Internal Modules: {len(loaded_skills)}\n"
        f"Module Sample: {', '.join(loaded_skills[:10])}...\n"
        f"All systems nominal."
    )
    
    return report
