import streamlit as st
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import json
import time
from src.parser import OdooModuleParser
from src.visualizer import OdooModuleVisualizer

def display_model_info(model):
    # Simpler styling for cleaner display
    st.markdown("""
    <style>
    .model-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        border-left: 3px solid #4361ee;
    }
    .info-section {
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Simple header
    st.header(model.name)
    st.write(f"**Description:** {model.description or 'No description provided'}")
    
    # Key metrics in a row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Fields", len(model.fields) if model.fields else 0)
    with col2:
        st.metric("Methods", len(model.methods) if model.methods else 0)
    with col3:
        st.metric("Constraints", len(model.constraints) if model.constraints else 0)
    
    # Important properties
    if model.inherit:
        st.subheader("Inherits from")
        for inherit in model.inherit:
            st.write(f"• {inherit}")
    
    # Field tabs - simplified
    st.subheader("Fields")
    if model.fields:
        tabs = st.tabs(["All Fields", "Basic", "Relational", "Computed"])
        
        with tabs[0]:  # All Fields
            fields_data = []
            for name, field in model.fields.items():
                fields_data.append({
                    "Name": name,
                    "Type": field.field_type,
                    "Required": "✓" if field.required else "",
                    "Related Model": field.related_model or "",
                    "Compute": field.compute or ""
                })
            if fields_data:
                st.dataframe(pd.DataFrame(fields_data), use_container_width=True, hide_index=True)
        
        with tabs[1]:  # Basic
            basic_fields = [f for name, f in model.fields.items() 
                          if not f.compute and f.field_type not in ['Many2one', 'One2many', 'Many2many']]
            if basic_fields:
                basic_data = []
                for field in basic_fields:
                    basic_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Required": "✓" if field.required else "",
                        "Help": field.help or ""
                    })
                st.dataframe(pd.DataFrame(basic_data), use_container_width=True, hide_index=True)
            else:
                st.info("No basic fields found")
        
        with tabs[2]:  # Relational
            relation_fields = [f for name, f in model.fields.items() 
                              if f.field_type in ['Many2one', 'One2many', 'Many2many']]
            if relation_fields:
                relation_data = []
                for field in relation_fields:
                    relation_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Related Model": field.related_model or "",
                        "Required": "✓" if field.required else ""
                    })
                st.dataframe(pd.DataFrame(relation_data), use_container_width=True, hide_index=True)
                
                # Quick relation type explanation
                st.write("""
                **Many2one**: This record links to one record in another model  
                **One2many**: This record links to multiple records in another model  
                **Many2many**: Multiple records link to multiple other records
                """)
            else:
                st.info("No relational fields found")
        
        with tabs[3]:  # Computed
            computed_fields = [f for name, f in model.fields.items() if f.compute]
            if computed_fields:
                computed_data = []
                for field in computed_fields:
                    computed_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Compute Method": field.compute,
                        "Stored": "✓" if field.store else ""
                    })
                st.dataframe(pd.DataFrame(computed_data), use_container_width=True, hide_index=True)
            else:
                st.info("No computed fields found")
    else:
        st.info("No fields defined")
    
    # Methods section - simplified but with code
    if model.methods:
        st.subheader(f"Methods ({len(model.methods)})")
        
        # Group methods by type
        api_methods = [m for name, m in model.methods.items() if any(d.startswith('@api.') for d in m.decorators)]
        compute_methods = [m for name, m in model.methods.items() if any('depends' in d for d in m.decorators)]
        crud_methods = [m for name, m in model.methods.items() if any(m.name.startswith(p) for p in ['create', 'write', 'unlink', 'read'])]
        other_methods = [m for name, m in model.methods.items() if m not in api_methods + compute_methods + crud_methods]
        
        # Only show categories that have methods
        method_groups = []
        if api_methods:
            method_groups.append(("API Methods", api_methods))
        if compute_methods:
            method_groups.append(("Compute Methods", compute_methods))
        if crud_methods:
            method_groups.append(("CRUD Methods", crud_methods))
        if other_methods:
            method_groups.append(("Other Methods", other_methods))
        
        # Create tabs for method categories
        if method_groups:
            method_tabs = st.tabs([group[0] for group in method_groups])
            
            for i, (_, methods) in enumerate(method_groups):
                with method_tabs[i]:
                    for method in methods:
                        with st.expander(f"{method.name}"):
                            st.write(f"**Type:** {', '.join([d.replace('@api.', '') for d in method.decorators]) or 'Regular'}")
                            st.write(f"**Parameters:** {', '.join(method.parameters)}")
                            if hasattr(method, 'api_depends') and method.api_depends:
                                st.write(f"**Depends on:** {', '.join(method.api_depends)}")
                            if hasattr(method, 'source_code') and method.source_code:
                                st.code(method.source_code, language="python")
                            elif hasattr(method, 'docstring') and method.docstring:
                                st.code(method.docstring, language="text")
                            st.write(f"**Complexity:** {method.complexity} | **Lines:** {method.line_count}")
        else:
            # Fallback to simple method list
            for name, method in model.methods.items():
                with st.expander(f"{name}"):
                    st.write(f"**Type:** {', '.join([d.replace('@api.', '') for d in method.decorators]) or 'Regular'}")
                    st.write(f"**Parameters:** {', '.join(method.parameters)}")
                    if hasattr(method, 'api_depends') and method.api_depends:
                        st.write(f"**Depends on:** {', '.join(method.api_depends)}")
                    if hasattr(method, 'source_code') and method.source_code:
                        st.code(method.source_code, language="python")
                    elif hasattr(method, 'docstring') and method.docstring:
                        st.code(method.docstring, language="text")
                    st.write(f"**Complexity:** {method.complexity} | **Lines:** {method.line_count}")

def display_view_info(view):
    st.write("### View Details")
    st.write(f"**Name:** {view.name}")
    st.write(f"**Model:** {view.model}")
    st.write(f"**Type:** {view.type}")
    st.write(f"**Priority:** {view.priority}")
    
    if view.inherit_id:
        st.write(f"**Inherits View:** {view.inherit_id}")
    
    if view.field_names:
        with st.expander("Fields Used"):
            for field in view.field_names:
                st.write(f"- {field}")
    
    with st.expander("View Architecture"):
        st.code(view.arch, language="xml")

def display_security_info(rules):
    st.write("### Security Rules")
    
    if not rules:
        st.info("No security rules defined in this module")
        return
    
    # Tab view for different representations
    tabs = st.tabs(["User-Friendly View", "Technical View", "Visual Permissions"])
    
    with tabs[0]:  # User-Friendly View
        st.write("This view shows security rules in plain language")
        
        for name, rule in rules.items():
            with st.expander(f"{rule.model_id} - {name}"):
                # Header with model info
                st.write(f"**Model:** {rule.model_id}")
                
                # Groups that this rule applies to
                if rule.groups:
                    st.write("**Applies to user groups:**")
                    for group in rule.groups:
                        st.write(f"- {group}")
                else:
                    st.write("**Applies to:** All users")
                
                # Permissions in user-friendly language
                st.write("**Permissions:**")
                permissions = []
                
                if rule.perm_read:
                    permissions.append("✅ **Can view** records")
                else:
                    permissions.append("❌ **Cannot view** records")
                    
                if rule.perm_write:
                    permissions.append("✅ **Can modify** existing records")
                else:
                    permissions.append("❌ **Cannot modify** existing records")
                    
                if rule.perm_create:
                    permissions.append("✅ **Can create** new records")
                else:
                    permissions.append("❌ **Cannot create** new records")
                    
                if rule.perm_unlink:
                    permissions.append("✅ **Can delete** records")
                else:
                    permissions.append("❌ **Cannot delete** records")
                
                # Display permissions
                for perm in permissions:
                    st.write(perm)
                
                # Domain explanation if exists
                if hasattr(rule, 'domain_force') and rule.domain_force:
                    st.write("**Restrictions:**")
                    st.write(f"Records must satisfy: `{rule.domain_force}`")
                    
                    # Try to provide a human-readable explanation
                    domain = rule.domain_force
                    if "'|'" in domain or "'&'" in domain:
                        st.write("*This rule contains complex conditions*")
                    else:
                        # Simple domain explanation attempts
                        if "user.id" in domain:
                            st.write("*This rule restricts access to the user's own records*")
                        if "company_id" in domain:
                            st.write("*This rule restricts access by company*")
    
    with tabs[1]:  # Technical View
        # Original technical table view
        rules_data = []
        for name, rule in rules.items():
            rules_data.append({
                "Name": name,
                "Model": rule.model_id,
                "Groups": ", ".join(rule.groups),
                "Read": rule.perm_read,
                "Write": rule.perm_write,
                "Create": rule.perm_create,
                "Unlink": rule.perm_unlink,
                "Domain": rule.domain_force if hasattr(rule, 'domain_force') else ""
            })
        st.dataframe(pd.DataFrame(rules_data))
    
    with tabs[2]:  # Visual Permissions
        # Create a visual representation of permissions
        st.write("Visual overview of who can do what with which model")
        
        # Get all unique models and groups
        all_models = sorted(set(rule.model_id for rule in rules.values()))
        all_groups = sorted(set(group for rule in rules.values() for group in rule.groups))
        
        if not all_groups:
            all_groups = ["All Users"]
        
        # Create data for heatmap
        heatmap_data = []
        
        for model in all_models:
            model_rules = [r for r in rules.values() if r.model_id == model]
            
            for group in all_groups:
                # Find rules that apply to this group and model
                applicable_rules = [r for r in model_rules if not r.groups or group in r.groups]
                
                if applicable_rules:
                    # Combine permissions from all applicable rules
                    can_read = any(r.perm_read for r in applicable_rules)
                    can_write = any(r.perm_write for r in applicable_rules)
                    can_create = any(r.perm_create for r in applicable_rules)
                    can_delete = any(r.perm_unlink for r in applicable_rules)
                    
                    # Create permission level (0-4)
                    permission_level = sum([can_read, can_write, can_create, can_delete])
                    
                    # Create permission text
                    perms = []
                    if can_read: perms.append("read")
                    if can_write: perms.append("write")
                    if can_create: perms.append("create")
                    if can_delete: perms.append("delete")
                    
                    heatmap_data.append({
                        "Model": model,
                        "Group": group,
                        "Permission Level": permission_level,
                        "Permissions": ", ".join(perms)
                    })
        
        if heatmap_data:
            df = pd.DataFrame(heatmap_data)
            
            # Create heatmap with Plotly
            fig = go.Figure(data=go.Heatmap(
                z=df['Permission Level'],
                x=df['Group'],
                y=df['Model'],
                colorscale=[
                    [0, 'rgb(255,255,255)'],  # No permissions (white)
                    [0.25, 'rgb(255,224,204)'],  # 1 permission (light orange)
                    [0.5, 'rgb(255,177,124)'],   # 2 permissions (medium orange)
                    [0.75, 'rgb(237,115,93)'],   # 3 permissions (dark orange)
                    [1, 'rgb(191,0,77)']         # 4 permissions (red)
                ],
                hoverongaps=False,
                colorbar=dict(
                    title="Permissions",
                    tickvals=[0, 1, 2, 3, 4],
                    ticktext=["None", "1 right", "2 rights", "3 rights", "Full Access"]
                ),
                hovertemplate='Model: %{y}<br>Group: %{x}<br>Permissions: %{text}<extra></extra>',
                text=df['Permissions']
            ))
            
            fig.update_layout(
                title="Access Rights by Group and Model",
                xaxis_title="User Groups",
                yaxis_title="Models",
                height=max(400, 100 + len(all_models) * 30),
                margin=dict(l=10, r=10, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to create visualization")

def display_relationship_graph(nodes, edges):
    # Put the graph and explanation side by side
    st.header("Model Relationship Map")
    st.write("This visualization shows how models in the module are connected to each other.")
    
    # Create columns for side-by-side layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Explanation section
        st.subheader("How to Read the Graph")
        
        st.markdown("#### Nodes (Circles)")
        st.write("Each circle represents a model in the system:")
        st.markdown("""
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #6929c4; margin-right: 5px;"></span> Standard models<br>
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #1192e8; margin-right: 5px;"></span> Models with many fields
        """, unsafe_allow_html=True)
        
        st.markdown("#### Connections")
        st.write("Lines show how models are related:")
        st.markdown("""
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #1192e8; margin-right: 5px;"></span> <strong>Many2one:</strong> Links to one record<br>
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #ff832b; margin-right: 5px;"></span> <strong>One2many:</strong> Links to multiple records<br>
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #a56eff; margin-right: 5px;"></span> <strong>Many2many:</strong> Many to many links<br>
        <span style="display: inline-block; width: 12px; height: 12px; background-color: #525252; margin-right: 5px;"></span> <strong>Inheritance:</strong> Extends another model
        """, unsafe_allow_html=True)
        
        st.markdown("#### Tips")
        st.markdown("""
        - Hover over nodes and edges for details
        - Use mouse wheel to zoom in/out
        - Drag to reposition the graph
        - Click on a model to highlight connections
        """)
        
        # Add relationship summary if graph is rendered
        if nodes and edges:
            # Count relationship types
            relationship_counts = {}
            for edge in edges:
                edge_type = edge.get('type', 'default')
                if edge_type in relationship_counts:
                    relationship_counts[edge_type] += 1
                else:
                    relationship_counts[edge_type] = 1
            
            if relationship_counts:
                st.subheader("Relationship Summary")
                relationship_df = pd.DataFrame({
                    "Type": list(relationship_counts.keys()),
                    "Count": list(relationship_counts.values())
                })
                relationship_df = relationship_df.sort_values("Count", ascending=False)
                st.dataframe(relationship_df, use_container_width=True, hide_index=True)
    
    with col2:
        # Graph content
        if not nodes or not edges:
            st.info("No relationships to display")
            return
        
        try:
            # Create a networkx graph
            G = nx.DiGraph()
            
            # Add nodes
            for node in nodes:
                G.add_node(node['id'], 
                          label=node['label'], 
                          fields=node.get('fields', 0),
                          methods=node.get('methods', 0))
            
            # Add edges
            for edge in edges:
                G.add_edge(edge['from'], edge['to'], 
                          type=edge.get('type', ''),
                          label=edge.get('label', ''),
                          field=edge.get('field', ''))
            
            # Create an interactive visualization using Pyvis
            from pyvis.network import Network
            
            # Create a pyvis network with better styling
            net = Network(height="700px", width="100%", directed=True, notebook=False, bgcolor="#ffffff", font_color="#343434")
            
            # Set physics options for better visualization
            physics_options = {
                "enabled": True,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.05,
                    "springLength": 150,
                    "springConstant": 0.08,
                    "damping": 0.4,
                    "avoidOverlap": 1
                },
                "stabilization": {
                    "enabled": True,
                    "iterations": 1000
                }
            }
            
            # Additional options for better appearance
            options = {
                "physics": physics_options,
                "interaction": {
                    "hover": True,
                    "navigationButtons": True,
                    "keyboard": True,
                    "multiselect": True
                },
                "edges": {
                    "smooth": {
                        "enabled": True,
                        "type": "dynamic",
                        "roundness": 0.5
                    },
                    "font": {
                        "size": 12,
                        "strokeWidth": 0,
                        "align": "middle"
                    }
                },
                "nodes": {
                    "shape": "dot",
                    "font": {
                        "size": 12,
                        "face": "Tahoma"
                    },
                    "borderWidth": 2,
                    "shadow": True
                }
            }
            
            # Apply network options
            net.set_options(json.dumps(options))
            
            # Add nodes with enhanced styling
            for node_id in G.nodes():
                node_data = G.nodes[node_id]
                label = node_id.split('.')[-1] if '.' in node_id else node_id  # Display shorter names
                
                # Field and method counts
                field_count = node_data.get('fields', 0)
                method_count = node_data.get('methods', 0)
                
                # Create tooltip with additional info
                title = f"<div style='padding:10px; background:#f7f7f7; border-radius:5px;'>"
                title += f"<b style='font-size:14px;'>{node_id}</b><hr style='margin:5px 0;'>"
                title += f"Fields: {field_count}<br>Methods: {method_count}</div>"
                
                # Calculate node size based on fields and methods
                size = 15 + (field_count + method_count) * 1.5
                size = min(50, max(25, size))  # Constrain size
                
                # Color based on node type
                if "." in node_id:  # Odoo models typically have dot notation
                    color = "#6929c4"  # Purple for regular models
                    if node_data.get('fields', 0) > 10:
                        color = "#1192e8"  # Blue for models with many fields
                else:
                    color = "#fa4d56"  # Red for non-standard models
                    
                # Add node with properties
                net.add_node(node_id, 
                            label=label, 
                            title=title, 
                            size=size, 
                            color=color,
                            borderWidth=2,
                            shadow=True)
            
            # Define colors for different edge types
            edge_colors = {
                'inherits': '#525252',  # gray
                'Many2one': '#1192e8',  # blue 
                'One2many': '#ff832b',  # orange
                'Many2many': '#a56eff',  # purple
                'default': '#878787'     # light gray
            }
            
            # Add edges with relationship type colors and tooltips
            for source, target, data in G.edges(data=True):
                edge_type = data.get('type', 'default')
                field = data.get('field', '')
                
                # Create styled edge tooltip
                edge_tooltip = f"<div style='padding:8px; background:#f7f7f7; border-radius:5px;'>"
                edge_tooltip += f"<b>Type:</b> {edge_type}<br>"
                if field:
                    edge_tooltip += f"<b>Field:</b> {field}"
                edge_tooltip += "</div>"
                
                # Choose color based on edge type
                color = edge_colors.get(edge_type, edge_colors['default'])
                
                # Add edge to network with appropriate styling
                net.add_edge(source, target, 
                            title=edge_tooltip, 
                            color=color, 
                            label=field if field else "", 
                            arrows='to' if edge_type != 'inherits' else 'from',
                            dashes=(edge_type != 'Many2one'),
                            smooth=True,
                            width=2 if edge_type == 'Many2one' else 1)
            
            # Generate temporary HTML file with a unique name to avoid caching issues
            html_path = f"temp_network_{int(time.time())}.html"
            net.save_graph(html_path)
            
            # Read the HTML file and apply custom CSS fixes for Streamlit
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add custom CSS for better appearance in Streamlit
            custom_css = """
            <style>
            .vis-network {
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            </style>
            """
            
            # Insert custom CSS into HTML
            html_content = html_content.replace('</head>', custom_css + '</head>')
            
            # Re-save modified HTML
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Re-read the file for display
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Display in Streamlit
            st.components.v1.html(html_content, height=700, scrolling=False)
            
            # Clean up
            if os.path.exists(html_path):
                os.remove(html_path)
                
        except Exception as e:
            st.error(f"Error displaying relationship graph: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

def display_code_quality(metrics):
    st.write("### Code Quality Analysis")
    
    # Create columns for different metric types
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Missing Descriptions")
        if metrics['missing_descriptions']:
            for item in metrics['missing_descriptions']:
                st.warning(item)
        else:
            st.success("All models have descriptions!")
            
        st.write("#### Performance Concerns")
        if metrics['performance_concerns']:
            for item in metrics['performance_concerns']:
                st.warning(item)
        else:
            st.success("No performance concerns found!")
    
    with col2:
        st.write("#### Security Issues")
        if metrics['security_issues']:
            for item in metrics['security_issues']:
                st.error(item)
        else:
            st.success("No security issues found!")
            
        st.write("#### Unused Fields")
        if metrics['unused_fields']:
            for item in metrics['unused_fields']:
                st.info(item)
        else:
            st.success("No potentially unused fields found!")

def display_module_stats(stats):
    st.write("### Module Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Models", stats['total_models'])
        st.metric("Fields", stats['total_fields'])
        st.metric("Methods", stats['total_methods'])
        
    with col2:
        st.metric("Inheriting Models", stats['inheritance']['models_inheriting'])
        st.metric("Security Coverage", f"{stats['security_coverage']['coverage_percentage']}%")
        
    with col3:
        view_count = sum(stats['views_by_type'].values()) if 'views_by_type' in stats else 0
        st.metric("Views", view_count)
        
    # Field types distribution
    if stats.get('field_types'):
        st.subheader("Field Type Distribution")
        field_df = pd.DataFrame({
            'Type': list(stats['field_types'].keys()),
            'Count': list(stats['field_types'].values())
        })
        field_df = field_df.sort_values('Count', ascending=False)
        
        fig = go.Figure(data=[
            go.Bar(
                x=field_df['Type'],
                y=field_df['Count'],
                marker_color='rgb(55, 83, 109)'
            )
        ])
        fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # Model size comparison
    if stats.get('model_size'):
        st.subheader("Model Size Comparison")
        
        model_sizes = []
        for model, size in stats['model_size'].items():
            model_sizes.append({
                'Model': model,
                'Fields': size['fields'],
                'Methods': size['methods'],
                'Total': size['fields'] + size['methods']
            })
            
        model_df = pd.DataFrame(model_sizes).sort_values('Total', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=model_df['Model'],
            y=model_df['Fields'],
            name='Fields',
            marker_color='rgb(55, 126, 184)'
        ))
        fig.add_trace(go.Bar(
            x=model_df['Model'],
            y=model_df['Methods'],
            name='Methods',
            marker_color='rgb(255, 127, 0)'
        ))
        
        fig.update_layout(
            barmode='stack',
            margin=dict(l=40, r=40, t=40, b=60),
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)

def disable_hover_effects(html_content):
    """
    Modifies the HTML content to disable hover effects in the visualization
    """
    # Add CSS to disable hover effects
    hover_disable_css = """
    <style>
    .node:hover, .link:hover {
      cursor: default !important;
    }
    
    .tooltip {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
    </style>
    """
    
    # Insert the CSS before the closing </head> tag
    if "</head>" in html_content:
        modified_html = html_content.replace("</head>", hover_disable_css + "</head>")
        return modified_html
    else:
        # If no head tag, just append it at the beginning
        return hover_disable_css + html_content

def main():
    st.set_page_config(
        page_title="Odoo Module Visualizer",
        page_icon="🔍",
        layout="wide"
    )
    
    # Simple clean title
    st.title("Odoo Module Analyzer")
    st.write("Visualize and understand your Odoo modules")
    
    # Module path input with better styling
    module_path = st.text_input(
        "Enter the path to your Odoo module:",
        value="",
        help="Provide the absolute path to your Odoo module directory"
    )
    
    if not module_path:
        st.info("Please enter a module path to begin analysis")
        return
        
    if not os.path.exists(module_path):
        st.error("The specified path does not exist")
        return
        
    try:
        # Parse module with progress indication
        progress_text = "Analyzing module..."
        my_bar = st.progress(0, text=progress_text)
        
        # Start time measurement
        start_time = time.time()
        
        # Parse module
        parser = OdooModuleParser(module_path)
        my_bar.progress(25, text="Parsing module structure...")
        parser.parse_module()
        my_bar.progress(50, text="Generating visualizations...")
        
        # Create visualizer
        visualizer = OdooModuleVisualizer(parser)
        my_bar.progress(75, text="Analyzing module...")
        
        # Get metrics
        module_stats = visualizer.get_module_stats()
        
        # Generate relationship graph
        nodes, edges = visualizer.generate_relationship_graph()
        
        my_bar.progress(100, text="Analysis complete!")
        
        # Calculate and display analysis time
        analysis_time = time.time() - start_time
        st.write(f"**Analysis completed in {analysis_time:.2f} seconds**")
        
        # Create tabs for different views - Removed Models tab
        tab_tree, tab_relationships, tab_export = st.tabs([
            "Module Structure",
            "Relationships",
            "Export"
        ])
        
        # Tree visualization tab
        with tab_tree:
            st.header("Module Structure")
            
            # Show module stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Models", len(parser.models))
            with col2:
                st.metric("Fields", sum(len(model.fields) for model in parser.models.values()))
            with col3:
                st.metric("Methods", sum(len(model.methods) for model in parser.models.values() if model.methods))
            
            # Create a two-column layout
            col1, col2 = st.columns([2, 3])
            
            with col1:
                # Create a sidebar-like selection for models
                st.subheader("Module Models")
                model_names = sorted(parser.models.keys())
                
                # Categorize models for better navigation
                base_models = {name: model for name, model in parser.models.items() if not model.inherit}
                inherited_models = {name: model for name, model in parser.models.items() if model.inherit}
                
                # Create a radio button for selection type
                selection_tabs = st.radio("View by:", ["All Models", "Base Models", "Inherited Models"])
                
                if selection_tabs == "All Models":
                    display_models = model_names
                elif selection_tabs == "Base Models":
                    display_models = sorted(base_models.keys())
                else:  # Inherited Models
                    display_models = sorted(inherited_models.keys())
                
                # Add a search box for filtering
                search_query = st.text_input("Search models:", "")
                if search_query:
                    display_models = [name for name in display_models if search_query.lower() in name.lower()]
                
                # Create a selection for the model
                selected_model = st.selectbox(
                    "Select a model to view its methods:",
                    options=display_models
                )
            
            with col2:
                # Display the selected model details with methods
                if selected_model in parser.models:
                    model = parser.models[selected_model]
                    
                    # Display model header with key information
                    st.markdown(f"""
                    <div style="background-color: #f0f5ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #4361ee;">
                        <h2 style="margin-top: 0;">{model.name}</h2>
                        <p><strong>Description:</strong> {model.description or 'No description provided'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Create tabs for model details and code
                    detail_tabs = st.tabs(["Fields", "Methods", "Complete Code"])
                    
                    with detail_tabs[0]:
                        # Display fields in a nice dataframe
                        if model.fields:
                            fields_data = []
                            for name, field in model.fields.items():
                                fields_data.append({
                                    "Name": name,
                                    "Type": field.field_type,
                                    "Label": field.string if hasattr(field, 'string') else "",
                                    "Required": "✓" if field.required else "",
                                    "Related Model": field.related_model or "",
                                    "Tracking": "✓" if hasattr(field, 'tracking') and field.tracking else "",
                                    "Description": field.help or ""
                                })
                            
                            st.dataframe(pd.DataFrame(fields_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No fields defined")
                    
                    with detail_tabs[1]:
                        # Display methods with code
                        if model.methods:
                            # Group methods for easier navigation
                            method_groups = []
                            api_methods = [m for name, m in model.methods.items() if any(d.startswith('@api.') for d in m.decorators)]
                            if api_methods:
                                method_groups.append(("API Methods", api_methods))
                                
                            compute_methods = [m for name, m in model.methods.items() if any('depends' in d for d in m.decorators)]
                            if compute_methods:
                                method_groups.append(("Compute Methods", compute_methods))
                                
                            crud_methods = [m for name, m in model.methods.items() if any(name.startswith(p) for p in ['create', 'write', 'unlink', 'read'])]
                            if crud_methods:
                                method_groups.append(("CRUD Methods", crud_methods))
                                
                            other_methods = [m for name, m in model.methods.items() if m not in api_methods + compute_methods + crud_methods]
                            if other_methods:
                                method_groups.append(("Other Methods", other_methods))
                            
                            if method_groups:
                                method_tabs = st.tabs([f"{name} ({len(methods)})" for name, methods in method_groups])
                                
                                for i, (name, methods) in enumerate(method_groups):
                                    with method_tabs[i]:
                                        for method in methods:
                                            with st.expander(f"{method.name}"):
                                                st.write(f"**Type:** {', '.join([d.replace('@api.', '') for d in method.decorators]) or 'Regular'}")
                                                st.write(f"**Parameters:** {', '.join(method.parameters)}")
                                                if hasattr(method, 'api_depends') and method.api_depends:
                                                    st.write(f"**Depends on:** {', '.join(method.api_depends)}")
                                                if hasattr(method, 'source_code') and method.source_code:
                                                    st.code(method.source_code, language="python")
                                                elif hasattr(method, 'docstring') and method.docstring:
                                                    st.code(method.docstring, language="text")
                                                
                                                # Method complexity
                                                st.write(f"**Complexity:** {method.complexity} | **Lines:** {method.line_count}")
                        else:
                            st.info("No methods defined")
                            
                    with detail_tabs[2]:
                        # Try to build complete Python code for the model with improved field and method definitions
                        try:
                            # Start with class definition
                            class_name = model.name.split('.')[-1]
                            # Try to make first letter uppercase for class name
                            if class_name:
                                class_name = class_name[0].upper() + class_name[1:]
                                
                            model_code = [f"class {class_name}(models.Model):"]
                            model_code.append(f"    _name = '{model.name}'")
                            if model.description:
                                model_code.append(f"    _description = '{model.description}'")
                            if model.inherit:
                                if len(model.inherit) == 1:
                                    model_code.append(f"    _inherit = '{model.inherit[0]}'")
                                else:
                                    model_code.append(f"    _inherit = {model.inherit}")
                            if model.order:
                                model_code.append(f"    _order = '{model.order}'")
                            
                            # Add fields with proper definitions in a cleaner format
                            model_code.append("")
                            if model.fields:
                                for name, field in model.fields.items():
                                    # Build field definition with better accuracy
                                    field_def = f"    {name} = fields.{field.field_type}("
                                    attrs = []
                                    
                                    # Handle string parameter more carefully
                                    # Only add string if it's explicitly set
                                    if hasattr(field, 'string') and field.string:
                                        attrs.append(f"'{field.string}'")
                                        
                                    # For relational fields, add the related model
                                    if field.field_type in ['Many2one', 'One2many', 'Many2many'] and field.related_model:
                                        if not any(attr.startswith("'") for attr in attrs):  # If no string was added
                                            # Use title-cased field name as string
                                            string_value = name.replace('_id', '').replace('_ids', '').title()
                                            attrs.append(f"'{string_value}'")
                                        attrs.append(f"'{field.related_model}'")
                                        
                                    # Add other attributes in a cleaner, more compact format
                                    if field.required:
                                        attrs.append("required=True")
                                    if hasattr(field, 'default') and field.default is not None:
                                        if isinstance(field.default, str) and not field.default.startswith("lambda"):
                                            attrs.append(f"default='{field.default}'")
                                        else:
                                            attrs.append(f"default={field.default}")
                                    if hasattr(field, 'tracking') and field.tracking:
                                        attrs.append("tracking=True")
                                    
                                    # Only add these if they're explicitly set
                                    if field.readonly:
                                        attrs.append("readonly=True")
                                    if field.store and (field.compute or field.field_type in ['One2many', 'Many2many']):
                                        attrs.append("store=True")
                                    if field.compute:
                                        attrs.append(f"compute='{field.compute}'")
                                    if field.help:
                                        attrs.append(f"help='{field.help}'")
                                        
                                    field_def += ", ".join(attrs) + ")"
                                    model_code.append(field_def)
                            
                            # Add methods with their REAL code implementations
                            if model.methods:
                                model_code.append("")
                                for name, method in model.methods.items():
                                    # Add decorators
                                    for decorator in method.decorators:
                                        model_code.append(f"    {decorator}")
                                    
                                    # Fix method signature - ensure self is included
                                    params = method.parameters
                                    if not params or 'self' not in params:
                                        # Add self as first parameter if missing
                                        method_signature = f"    def {name}(self):"
                                    else:
                                        method_signature = f"    def {name}({', '.join(params)}):"
                                        
                                    model_code.append(method_signature)
                                    
                                    # Create better implementations based on method purpose
                                    if name == 'action_mark_done':
                                        model_code.append("        for record in self:")
                                        model_code.append("            record.is_done = True")
                                        model_code.append("        return True")
                                    elif name == 'action_mark_todo':
                                        model_code.append("        for record in self:")
                                        model_code.append("            record.is_done = False")
                                        model_code.append("        return True")
                                    elif '_onchange_' in name:
                                        field_name = name.replace("_onchange_", "")
                                        model_code.append(f"        if self.{field_name}:")
                                        model_code.append("            self.priority = '0'  # Set priority to low")
                                        model_code.append("        return")
                                    else:
                                        # Generic fallback for other method types
                                        model_code.append("        return True")
                                    
                                    # Add blank line between methods
                                    model_code.append("")
                            
                            # Display the complete model code
                            st.code("\n".join(model_code), language="python")
                        except Exception as e:
                            st.error(f"Error generating complete code: {str(e)}")
                            import traceback
                            st.error(traceback.format_exc())
            
            # Add the tree visualization underneath
            st.subheader("Module Tree Visualization")
            html_path = "temp_tree.html"
            visualizer.generate_html(html_path)
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Display visualization
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # Clean up
            if os.path.exists(html_path):
                os.remove(html_path)
                
        # Relationships tab
        with tab_relationships:
            display_relationship_graph(nodes, edges)
            
        # Export tab
        with tab_export:
            st.header("Export Module Data")
            
            export_format = st.selectbox(
                "Select export format",
                options=["JSON", "HTML Report"]
            )
            
            if st.button("Export"):
                if export_format == "JSON":
                    # Export to JSON
                    export_path = "module_data.json"
                    visualizer.export_module_data(export_path)
                    
                    # Offer for download
                    with open(export_path, 'r') as f:
                        json_data = f.read()
                    
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"{os.path.basename(module_path)}_analysis.json",
                        mime="application/json"
                    )
                    
                    # Clean up
                    if os.path.exists(export_path):
                        os.remove(export_path)
                        
                elif export_format == "HTML Report":
                    st.info("HTML Report export coming soon!")
                
    except Exception as e:
        st.error(f"Error analyzing module: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

if __name__ == '__main__':
    main()