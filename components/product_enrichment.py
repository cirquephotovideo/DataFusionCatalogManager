import streamlit as st
from services.ai_service import AIService
from services.catalog_service import CatalogService
from services.competitor_service import CompetitorService
import asyncio
from datetime import datetime
import pandas as pd
import math
import json

def format_datetime(dt):
    """Format datetime for display"""
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M")
    return "-"

def safe_lower(value):
    """Safely convert value to lowercase string"""
    if value is None:
        return ""
    return str(value).lower()

async def enrich_with_ai(ai_service, product_id: str, model: str, prompt_index: int = None):
    """Enrich product details using specified AI model and selected prompts"""
    product = CatalogService.get_catalog(product_id)
    
    # Get configured prompts or use defaults
    prompts = st.session_state.get('enrichment_prompts', [
        "Create a detailed product description focusing on features and benefits",
        "Generate technical specifications in a structured format",
        "Suggest SEO-optimized product title and meta description",
        "List main product features and use cases",
        "Generate relevant product categories and tags",
        "Create a marketing-focused product description highlighting unique selling points"
    ])
    
    # If prompt_index is provided, only process that specific prompt
    if prompt_index is not None:
        prompts = [prompts[prompt_index]]
    
    results = []
    for prompt in prompts:
        full_prompt = f"""
        Generate a response in pure HTML format using only <p>, <strong>, <ul>, <li> tags.
        The product name is: {product.get('name', '')}
        With information:
        - Description: {product.get('description', '')}
        - Technical Details: {product.get('technical_details', '')}
        - Barcode: {product.get('barcode', '')}
        - Article Code: {product.get('article_code', '')}
        
        Task: {prompt}
        
        Respond in a structured HTML format without any markdown or code blocks.
        """
        
        try:
            response = await ai_service.generate_content(full_prompt, model)
            results.append({
                "prompt": prompt,
                "response": response.strip()
            })
        except Exception as e:
            results.append({
                "prompt": prompt,
                "error": str(e)
            })
    
    return True, results

def render_enrichment_results(results):
    """Render AI enrichment results in a block layout"""
    # Create columns for results (2 columns)
    cols = st.columns(2)
    
    for idx, result in enumerate(results):
        with cols[idx % 2]:
            st.markdown("---")
            st.subheader(f"📝 {result['prompt']}")
            if "error" in result:
                st.error(f"Error: {result['error']}")
            else:
                # Display HTML content directly
                st.markdown(result['response'], unsafe_allow_html=True)

def render_editable_field(label: str, value: str, key: str):
    """Render an editable field with edit button"""
    col1, col2 = st.columns([4, 1])
    with col1:
        if f"editing_{key}" in st.session_state and st.session_state[f"editing_{key}"]:
            new_value = st.text_area(label, value=value, key=f"input_{key}")
            if st.button("Save", key=f"save_{key}"):
                st.session_state[f"editing_{key}"] = False
                return new_value, True
            if st.button("Cancel", key=f"cancel_{key}"):
                st.session_state[f"editing_{key}"] = False
                return value, False
        else:
            st.write(f"{label}: {value}")
    with col2:
        if f"editing_{key}" not in st.session_state or not st.session_state[f"editing_{key}"]:
            if st.button("✏️", key=f"edit_{key}"):
                st.session_state[f"editing_{key}"] = True
                st.rerun()
    return value, False

def render_product_card(product, ai_service):
    """Render a product card with AI enrichment buttons and editable fields"""
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Editable fields
            name, name_changed = render_editable_field("Name", product.get('name', 'No Name'), f"name_{product['id']}")
            description, desc_changed = render_editable_field("Description", product.get('description', 'No description'), f"desc_{product['id']}")
            article_code, code_changed = render_editable_field("Article Code", product.get('article_code', 'N/A'), f"code_{product['id']}")
            barcode, barcode_changed = render_editable_field("Barcode", product.get('barcode', 'N/A'), f"barcode_{product['id']}")
            
            # If any field was changed, update the product
            if any([name_changed, desc_changed, code_changed, barcode_changed]):
                updated_product = product.copy()
                if name_changed: updated_product['name'] = name
                if desc_changed: updated_product['description'] = description
                if code_changed: updated_product['article_code'] = article_code
                if barcode_changed: updated_product['barcode'] = barcode
                
                # Update product in database
                success = CatalogService.update_catalog(product['id'], updated_product)
                if success:
                    st.success("Product updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update product")
            
            # Non-editable fields
            st.write(f"Stock: {product.get('stock_quantity', '0')}")
            if product.get('purchase_price'):
                st.write(f"Purchase Price (HT): €{product['purchase_price']}")
            if product.get('price'):
                st.write(f"Selling Price: €{product['price']}")
            st.write(f"Last Updated: {format_datetime(product.get('last_updated'))}")
            st.write(f"Source: {product.get('source', 'Unknown')}")
        
        with col2:
            st.markdown("### AI Enrichment")
            
            # Get current AI config
            current_config = ai_service.get_active_config()
            if not current_config:
                st.warning("⚠️ AI not configured. Please set up AI Settings first.")
                return
            
            # Generate All button
            if st.button("🔄 Generate All Content", key=f"all_{product['id']}", use_container_width=True):
                with st.spinner("Generating all content..."):
                    success, results = asyncio.run(enrich_with_ai(
                        ai_service,
                        product['id'],
                        current_config['model']
                    ))
                    if success:
                        st.success("Content generation completed!")
                        render_enrichment_results(results)
                    else:
                        st.error(f"Generation failed: {results}")
            
            # Individual prompt buttons
            st.markdown("### Generate Individual Sections")
            prompts = st.session_state.get('enrichment_prompts', [])
            for idx, prompt in enumerate(prompts):
                if st.button(f"📝 {prompt[:30]}...", key=f"prompt_{idx}_{product['id']}", use_container_width=True):
                    with st.spinner(f"Generating content for prompt {idx + 1}..."):
                        success, results = asyncio.run(enrich_with_ai(
                            ai_service,
                            product['id'],
                            current_config['model'],
                            idx
                        ))
                        if success:
                            st.success("Content generation completed!")
                            render_enrichment_results(results)
                        else:
                            st.error(f"Generation failed: {results}")

def render_product_enrichment():
    """Main product enrichment interface"""
    st.title("Product Enrichment")

    # Initialize services
    if 'ai_service' not in st.session_state:
        st.session_state.ai_service = AIService()

    # Search and filter section
    st.subheader("Search Products")
    search_term = st.text_input("Search by name, reference, or article code")
    
    # Get products
    products = CatalogService.get_catalogs()
    if not products:
        st.warning("No products found in the catalog")
        return

    # Filter products
    if search_term:
        search_term_lower = search_term.lower()
        filtered_products = [p for p in products if 
            search_term_lower in safe_lower(p.get('name')) or
            search_term_lower in safe_lower(p.get('reference')) or
            search_term_lower in safe_lower(p.get('article_code'))]
    else:
        filtered_products = products

    # Pagination
    items_per_page = 10
    total_pages = math.ceil(len(filtered_products) / items_per_page)
    
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 1

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.write(f"Page {st.session_state.page_number} of {total_pages}")

    # Calculate slice indices
    start_idx = (st.session_state.page_number - 1) * items_per_page
    end_idx = start_idx + items_per_page
    page_products = filtered_products[start_idx:end_idx]

    # Display products
    for product in page_products:
        render_product_card(product, st.session_state.ai_service)

    # Pagination navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.session_state.page_number > 1:
            if st.button("Previous Page"):
                st.session_state.page_number -= 1
                st.rerun()
    with col3:
        if st.session_state.page_number < total_pages:
            if st.button("Next Page"):
                st.session_state.page_number += 1
                st.rerun()
