import streamlit as st
import pandas as pd
from utils.processors import generate_fusion_code
from services.catalog_service import CatalogService

def render_matching_engine():
    st.header("Product Matching")
    
    catalogs = CatalogService.get_catalogs()
    df = pd.DataFrame(catalogs)
    
    if not df.empty:
        st.subheader("Match Products")
        
        # Matching criteria
        match_type = st.radio(
            "Select matching criteria",
            ["Article Code", "Barcode", "Name"]
        )
        
        if match_type == "Article Code":
            matches = df[df.duplicated(subset=['article_code'], keep=False)]
        elif match_type == "Barcode":
            # Only match non-empty barcodes
            matches = df[df['barcode'].notna()]
            matches = matches[matches.duplicated(subset=['barcode'], keep=False)]
        else:
            # Match by name if name is not empty
            matches = df[df['name'].notna()]
            matches = matches[matches.duplicated(subset=['name'], keep=False)]
        
        if not matches.empty:
            # Add supplier info to display
            matches_display = matches.copy()
            matches_display['price_range'] = matches_display.apply(
                lambda x: f"€{min([sp['price'] for sp in x['supplier_prices']] + [x['price']]):.2f} - €{max([sp['price'] for sp in x['supplier_prices']] + [x['price']]):.2f}" if x['supplier_prices'] else f"€{x['price']:.2f}",
                axis=1
            )
            
            # Display columns in a meaningful order
            display_columns = ['article_code', 'name', 'description', 'barcode', 'price_range', 'stock_quantity']
            st.write("Matched Products:")
            st.dataframe(matches_display[display_columns])
            
            if st.button("Generate Fusion Catalog"):
                # Generate fusion codes using article code as base
                matches['fusion_code'] = matches.apply(
                    lambda x: generate_fusion_code(x['article_code'], x['article_code'].split('-')[0] if '-' in x['article_code'] else x['article_code']),
                    axis=1
                )
                
                # Prepare fusion catalog with relevant columns
                fusion_catalog = matches[['fusion_code', 'article_code', 'name', 'description', 'barcode', 'price', 'stock_quantity', 'purchase_price', 'eco_value']]
                
                st.write("Fusion Catalog:")
                st.dataframe(fusion_catalog)
                
                # Download option
                csv = fusion_catalog.to_csv(index=False)
                st.download_button(
                    "Download Fusion Catalog",
                    csv,
                    "fusion_catalog.csv",
                    "text/csv",
                    help="Download the fusion catalog as a CSV file"
                )
                
                # Show matching statistics
                st.subheader("Matching Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Products", len(df))
                with col2:
                    st.metric("Matched Products", len(matches))
                with col3:
                    st.metric("Match Rate", f"{(len(matches)/len(df)*100):.1f}%")
        else:
            st.info("No matching products found with the selected criteria.")
    else:
        st.info("No catalogs available for matching. Please import some products first.")
