import streamlit as st
from services.competitor_service import CompetitorService
from services.catalog_service import CatalogService
import pandas as pd
from datetime import datetime
import asyncio

def render_price_scraping():
    st.title("Price Scraping")
    
    # Initialize competitor service
    if 'competitor_service' not in st.session_state:
        st.session_state.competitor_service = CompetitorService()

    # Competitor configuration section
    st.header("Competitor Sites")
    
    # Add new competitor
    with st.form("add_competitor"):
        st.subheader("Add New Competitor")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Competitor Name")
            base_url = st.text_input("Base URL")
        with col2:
            price_selector = st.text_input("Price Selector (CSS)")
            st.info("Example: .product-price, #price, .price-value")
        
        if st.form_submit_button("Add Competitor"):
            if name and base_url and price_selector:
                if st.session_state.competitor_service.add_competitor(name, base_url, price_selector):
                    st.success(f"Added competitor: {name}")
                else:
                    st.error("Failed to add competitor")
            else:
                st.error("All fields are required")

    # List existing competitors
    st.subheader("Configured Competitors")
    competitors = st.session_state.competitor_service.get_competitors()
    
    if competitors:
        for name, config in competitors.items():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{name}**")
            with col2:
                st.write(config['url'])
            with col3:
                if st.button("Remove", key=f"remove_{name}"):
                    if st.session_state.competitor_service.remove_competitor(name):
                        st.success(f"Removed competitor: {name}")
                        st.rerun()
    else:
        st.info("No competitors configured yet")

    # Schedule scraping
    st.markdown("---")
    st.header("Schedule Price Scraping")
    
    col1, col2 = st.columns(2)
    with col1:
        schedule_enabled = st.checkbox("Enable Scheduled Scraping")
        if schedule_enabled:
            schedule_time = st.time_input("Daily Scraping Time")
            if st.button("Save Schedule"):
                st.success("Scraping schedule saved")
    
    with col2:
        if st.button("Run Scraping Now", use_container_width=True):
            with st.spinner("Scraping competitor prices..."):
                products = CatalogService.get_catalogs()
                progress_bar = st.progress(0)
                results = []
                
                for i, product in enumerate(products):
                    # Update progress
                    progress = (i + 1) / len(products)
                    progress_bar.progress(progress)
                    
                    # Get competitor prices
                    prices = asyncio.run(st.session_state.competitor_service.get_competitor_prices(product['reference']))
                    if prices:
                        results.append({
                            'Product': product.get('name', 'Unknown'),
                            'Our Price': product.get('price', 0),
                            **prices
                        })
                
                if results:
                    st.success(f"Scraped prices for {len(results)} products")
                    st.dataframe(pd.DataFrame(results))
                else:
                    st.warning("No prices found")

def render_price_matching():
    st.title("Price Matching")
    
    # Initialize services
    if 'competitor_service' not in st.session_state:
        st.session_state.competitor_service = CompetitorService()

    # Get products
    products = CatalogService.get_catalogs()
    if not products:
        st.warning("No products found in catalog")
        return

    # Filter and search
    search = st.text_input("Search products")
    
    filtered_products = products
    if search:
        search = search.lower()
        filtered_products = [p for p in products if 
            search in str(p.get('name', '')).lower() or
            search in str(p.get('reference', '')).lower() or
            search in str(p.get('article_code', '')).lower()]

    # Display products with competitor prices
    for product in filtered_products:
        with st.expander(f"{product.get('name', 'Unknown Product')} ({product.get('reference', 'No Ref')})"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Our Price:**", f"€{product.get('price', 0):.2f}")
                if product.get('purchase_price'):
                    margin_info = st.session_state.competitor_service.calculate_margin(
                        float(product['purchase_price']),
                        float(product.get('price', 0))
                    )
                    margin_color = "green" if margin_info['is_profitable'] else "red"
                    st.markdown(f"**Margin:** <span style='color:{margin_color}'>{margin_info['margin_percentage']:.1f}%</span>", unsafe_allow_html=True)
            
            with col2:
                if st.button("Fetch Competitor Prices", key=f"fetch_{product['id']}"):
                    with st.spinner("Fetching prices..."):
                        prices = asyncio.run(st.session_state.competitor_service.get_competitor_prices(product['reference']))
                        if prices:
                            st.write("**Competitor Prices:**")
                            for competitor, price in prices.items():
                                st.write(f"{competitor}: €{price:.2f}")
                            
                            # Price validation
                            validation = st.session_state.competitor_service.validate_pricing_strategy(
                                float(product.get('price', 0)),
                                prices
                            )
                            if validation['messages']:
                                for msg in validation['messages']:
                                    st.warning(msg)
                        else:
                            st.info("No competitor prices found")

def render_competitor_analysis():
    st.title("Competitor Analysis")
    
    # Initialize competitor service
    if 'competitor_service' not in st.session_state:
        st.session_state.competitor_service = CompetitorService()

    # Get all price data
    products = CatalogService.get_catalogs()
    if not products:
        st.warning("No products found in catalog")
        return

    # Fetch prices button
    if st.button("Fetch All Competitor Prices", use_container_width=True):
        with st.spinner("Fetching competitor prices..."):
            progress_bar = st.progress(0)
            price_data = []
            
            for i, product in enumerate(products):
                # Update progress
                progress = (i + 1) / len(products)
                progress_bar.progress(progress)
                
                if product.get('price'):
                    prices = asyncio.run(st.session_state.competitor_service.get_competitor_prices(product['reference']))
                    if prices:
                        price_data.append({
                            'Product': product.get('name', 'Unknown'),
                            'Our Price': product['price'],
                            **prices
                        })

            if price_data:
                # Convert to DataFrame for analysis
                df = pd.DataFrame(price_data)
                
                # Overall statistics
                st.header("Price Statistics")
                st.write("Average prices by seller:")
                st.write(df.mean().round(2))
                
                # Price difference analysis
                st.header("Price Comparison")
                competitors = df.columns[2:]  # Skip Product and Our Price columns
                for competitor in competitors:
                    diff = ((df[competitor] - df['Our Price']) / df['Our Price'] * 100).mean()
                    if diff > 0:
                        st.write(f"We are {abs(diff):.1f}% cheaper than {competitor}")
                    else:
                        st.write(f"We are {abs(diff):.1f}% more expensive than {competitor}")
                
                # Detailed comparison table
                st.header("Detailed Comparison")
                st.dataframe(df)
            else:
                st.info("No competitor price data available for analysis")
