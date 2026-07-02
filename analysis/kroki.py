import os
import tempfile
import subprocess
from datetime import datetime
import matplotlib.pyplot as plt

def kroki_it(fig=None, md_file="gallery.md"):
    """
    Saves a Matplotlib figure as SVG, encodes it via Kroki CLI (svgdraw),
    and appends the resulting Markdown snippet to a file.
    """
    # If no figure is passed, grab the current active Matplotlib figure
    if fig is None:
        fig = plt.gcf()
        
    # 1. Create a temporary file for the SVG
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as tmp:
        temp_svg_file = tmp.name
        
    try:
        # 2. Save the plot as SVG
        fig.savefig(temp_svg_file, format="svg", bbox_inches="tight")
        
        # 3. Call the Kroki CLI
        cmd = ["kroki", "-encode", temp_svg_file, "-type", "svgdraw"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        kroki_output = result.stdout.strip()
        
        # 4. Append to the Markdown file
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(md_file, "a", encoding="utf-8") as f:
            f.write(f"\n### Graph generated on {timestamp}\n")
            f.write(f"{kroki_output}\n\n")
            
        print(f"✅ Graph successfully encoded and appended to: {md_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Kroki CLI: {e.stderr}")
    except FileNotFoundError:
        print("❌ Error: 'kroki' CLI tool not found. Is it installed and in your PATH?")
    finally:
        # 5. Clean up the temporary file
        if os.path.exists(temp_svg_file):
            os.remove(temp_svg_file)