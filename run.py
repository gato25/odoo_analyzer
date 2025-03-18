import os
import sys
import streamlit.web.cli as stcli
from pathlib import Path

def main():
    current_dir = Path(__file__).parent.resolve()
    os.chdir(current_dir)
    
    # Set up Streamlit command
    sys.argv = ["streamlit", "run", "src/app.py", "--theme.base", "light"]
    
    # Run Streamlit
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 