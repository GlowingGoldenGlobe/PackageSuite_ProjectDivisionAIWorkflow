# GUI Integration Module for System Chart Generation

import tkinter as tk
from tkinter import ttk
import os
import threading
import sys
from pathlib import Path

# Add parent directory to path to import chart_generator
sys.path.append(str(Path(__file__).parent.parent))
from utils import chart_generator

class SystemChartTab:
    """System Architecture Chart Tab for the GlowingGoldenGlobe GUI"""
    
    def __init__(self, parent_notebook):
        """
        Initialize the System Chart tab
        
        Args:
            parent_notebook: The parent ttk.Notebook widget
        """
        self.parent = parent_notebook
        self.tab = ttk.Frame(parent_notebook)
        parent_notebook.add(self.tab, text="System Charts")
        
        self.chart_generator = chart_generator.ChartGenerator(Path(__file__).parent.parent)
        
        # Status variables
        self.status_var = tk.StringVar(value="Ready to generate charts")
        self.progress_var = tk.DoubleVar(value=0)
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create widgets for the System Chart tab"""
        # Main layout frame
        main_frame = ttk.Frame(self.tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="System Architecture Charts", 
                                font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Chart type selection frame
        selection_frame = ttk.LabelFrame(main_frame, text="Chart Type")
        selection_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Chart options
        self.chart_type_var = tk.StringVar(value="ai_manager")
        
        ttk.Radiobutton(selection_frame, text="AI Managers Chart", 
                        variable=self.chart_type_var, value="ai_manager").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(selection_frame, text="Complete System Architecture", 
                        variable=self.chart_type_var, value="system").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Radiobutton(selection_frame, text="Both Charts", 
                        variable=self.chart_type_var, value="both").pack(anchor=tk.W, padx=10, pady=5)
        
        # Output location frame
        output_frame = ttk.LabelFrame(main_frame, text="Output Location")
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Default to docs folder
        docs_dir = os.path.join(Path(__file__).parent.parent, "docs")
        if not os.path.exists(docs_dir):
            os.makedirs(docs_dir, exist_ok=True)
        
        self.output_path_var = tk.StringVar(value=docs_dir)
        ttk.Label(output_frame, text="Charts will be saved to:").pack(anchor=tk.W, padx=10, pady=5)
        ttk.Label(output_frame, textvariable=self.output_path_var, 
                 foreground="blue").pack(anchor=tk.W, padx=10, pady=5)
        
        # Actions frame
        actions_frame = ttk.Frame(main_frame)
        actions_frame.pack(fill=tk.X, padx=10, pady=20)
        
        # Generate button with nice styling
        generate_btn = ttk.Button(actions_frame, text="Generate Chart", 
                                 command=self._generate_chart)
        generate_btn.pack(side=tk.LEFT, padx=10)
        
        view_btn = ttk.Button(actions_frame, text="View Last Chart", 
                             command=self._view_chart)
        view_btn.pack(side=tk.LEFT, padx=10)
        
        # Progress and status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
        
        progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, 
                                      length=100, variable=self.progress_var, 
                                      mode='indeterminate')
        progress_bar.pack(fill=tk.X, padx=10, pady=10)
        
        # Results section
        self.result_frame = ttk.LabelFrame(main_frame, text="Generated Charts")
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=10, 
                                  width=50, state=tk.DISABLED)
        self.result_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _generate_chart(self):
        """Generate the selected chart type"""
        self.status_var.set("Generating chart...")
        self.progress_var.set(0)
        
        # Start progress animation
        self._toggle_progress_animation(True)
        
        # Run in a separate thread to prevent GUI freezing
        threading.Thread(target=self._generate_chart_thread, daemon=True).start()
    
    def _generate_chart_thread(self):
        """Thread function to generate charts"""
        chart_type = self.chart_type_var.get()
        output_dir = self.output_path_var.get()
        
        try:
            # Collect data for chart generation
            self.chart_generator.collect_data()
            
            generated_files = []
            
            # Generate AI Manager chart
            if chart_type in ["ai_manager", "both"]:
                ai_chart_path = os.path.join(output_dir, "generated_ai_managers_chart.md")
                self.chart_generator.save_chart('ai_manager', ai_chart_path)
                generated_files.append(("AI Managers Chart", ai_chart_path))
            
            # Generate System Architecture chart
            if chart_type in ["system", "both"]:
                sys_chart_path = os.path.join(output_dir, "generated_system_architecture.md")
                self.chart_generator.save_chart('system', sys_chart_path)
                generated_files.append(("System Architecture Chart", sys_chart_path))
            
            # Update result text with generated files
            self._update_result_text(generated_files)
            
            # Update status
            self.status_var.set(f"{len(generated_files)} chart(s) generated successfully")
        
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
        
        finally:
            # Stop progress animation
            self._toggle_progress_animation(False)
    
    def _toggle_progress_animation(self, start=True):
        """Toggle progress bar animation"""
        if start:
            self.tab.after(50, self._update_progress_animation)
        else:
            self.progress_var.set(0)
    
    def _update_progress_animation(self):
        """Update progress bar for animation effect"""
        current = self.progress_var.get()
        if current < 100:
            self.progress_var.set(current + 1)
        else:
            self.progress_var.set(0)
        
        # Continue animation if status indicates processing
        if "Generating" in self.status_var.get():
            self.tab.after(50, self._update_progress_animation)
    
    def _update_result_text(self, generated_files):
        """Update the result text with generated files"""
        # Enable text widget for editing
        self.result_text.config(state=tk.NORMAL)
        
        # Clear previous content
        self.result_text.delete(1.0, tk.END)
        
        # Add new content
        self.result_text.insert(tk.END, "Generated charts:\n\n")
        
        for name, path in generated_files:
            self.result_text.insert(tk.END, f"• {name}:\n")
            self.result_text.insert(tk.END, f"  {path}\n\n")
        
        self.result_text.insert(tk.END, "To view the charts, open these files in a Markdown viewer " 
                               "that supports Mermaid diagrams, such as VS Code or GitHub.")
        
        # Disable editing
        self.result_text.config(state=tk.DISABLED)
    
    def _view_chart(self):
        """View the last generated chart"""
        chart_type = self.chart_type_var.get()
        output_dir = self.output_path_var.get()
        
        if chart_type == "both":
            chart_type = "ai_manager"  # Default to AI Manager chart
        
        file_name = f"generated_{chart_type}s_chart.md"
        file_path = os.path.join(output_dir, file_name.replace("systems_", "system_"))
        
        if os.path.exists(file_path):
            # Try to open the file with the system's default application
            try:
                import webbrowser
                webbrowser.open(file_path)
            except:
                self.status_var.set(f"Unable to open file. Path: {file_path}")
        else:
            self.status_var.set(f"File not found: {file_path}")


# Example of how to integrate this into the main GUI
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Chart Generator Test")
    root.geometry("800x600")
    
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True)
    
    # Create our tab
    chart_tab = SystemChartTab(notebook)
    
    # Add a dummy tab
    dummy_tab = ttk.Frame(notebook)
    notebook.add(dummy_tab, text="Main")
    
    root.mainloop()
