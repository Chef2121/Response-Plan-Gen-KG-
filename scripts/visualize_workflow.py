"""Workflow visualization script based on notebook implementation."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def visualize_workflow():
    """Visualize the workflow graph like in the notebook."""
    try:
        from src.workflows.graph import create_workflow
        
        # Create the workflow
        app = create_workflow()
        
        print("🎨 Generating workflow visualization...")
        
        # Generate the Mermaid PNG like in the notebook
        try:
            graph_image = app.get_graph().draw_mermaid_png()
            
            # Save the image
            with open("workflow_diagram.png", "wb") as f:
                f.write(graph_image)
            
            print("✅ Workflow diagram saved as workflow_diagram.png")
            
            # Also print the Mermaid source
            mermaid_source = app.get_graph().draw_mermaid()
            print("\n📊 Mermaid Source Code:")
            print("=" * 50)
            print(mermaid_source)
            print("=" * 50)
            
            return True
            
        except Exception as viz_error:
            print(f"❌ Visualization error: {viz_error}")
            print("💡 Make sure you have the required visualization dependencies")
            return False
            
    except Exception as e:
        print(f"❌ Error creating workflow: {e}")
        return False

if __name__ == "__main__":
    print("🔄 WORKFLOW VISUALIZATION")
    print("=" * 50)
    
    success = visualize_workflow()
    
    if success:
        print("\n✅ Visualization complete!")
        print("📁 Check workflow_diagram.png for the visual representation")
    else:
        print("\n❌ Visualization failed!")
        print("💡 Check your environment setup and dependencies")
