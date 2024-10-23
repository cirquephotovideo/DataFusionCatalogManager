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
            ["Article Code", "Barcode"]
        )
        
        if match_type == "Article Code":
            matches = df[df.duplicated(subset=['article_code'], keep=False)]
        else:
            matches = df[df.duplicated(subset=['barcode'], keep=False)]
        
        if not matches.empty:
            st.write("Matched Products:")
            st.dataframe(matches)
            
            if st.button("Generate Fusion Catalog"):
                # Generate fusion codes for matched products
                matches['fusion_code'] = matches.apply(
                    lambda x: generate_fusion_code(x['article_code'], x['brand']),
                    axis=1
                )
                
                st.write("Fusion Catalog:")
                st.dataframe(matches)
                
                # Download option
                csv = matches.to_csv(index=False)
                st.download_button(
                    "Download Fusion Catalog",
                    csv,
                    "fusion_catalog.csv",
                    "text/csv"
                )
        else:
            st.info("No matching products found.")
    else:
        st.info("No catalogs available for matching.")
