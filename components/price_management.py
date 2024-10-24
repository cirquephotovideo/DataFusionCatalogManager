import streamlit as st
from components.web_scraper import WebScraper
import pandas as pd
from datetime import datetime
import json
import asyncio

def render_price_scraping():
    """Render price scraping interface with web scraper integration"""
    st.title("Price Scraping")

    # Initialize web scraper if not exists
    if 'web_scraper' not in st.session_state:
        st.session_state.web_scraper = WebScraper()

    # Initialize saved rules if not exists
    if 'saved_scraping_rules' not in st.session_state:
        st.session_state.saved_scraping_rules = {}

    # Tabs for different scraping methods
    tab1, tab2, tab3 = st.tabs(["Quick Scrape", "Advanced Scraping", "Saved Rules"])

    with tab1:
        st.subheader("Quick Price Scraping")
        
        # URL input
        url = st.text_input("Enter competitor URL")
        
        # Multi-page settings
        max_pages = st.number_input("Maximum pages to scrape", min_value=1, value=5, key="quick_max_pages")
        
        if url:
            # Default fields for price scraping
            default_fields = ["name", "price", "sku", "availability"]
            
            if st.button("Quick Scrape", type="primary"):
                with st.spinner("Analyzing and scraping..."):
                    # Use the web scraper with default settings
                    model_provider = "ollama" if "mistral" in st.session_state.web_scraper.get_available_models()["Ollama"] else "openai"
                    model_name = "mistral" if model_provider == "ollama" else "gpt-3.5-turbo"
                    
                    # Generate rules
                    rules = asyncio.run(
                        st.session_state.web_scraper.generate_scraping_rules(
                            url,
                            default_fields,
                            model_provider,
                            model_name
                        )
                    )
                    
                    if rules and "selectors" in rules:
                        # Execute scraping
                        results = st.session_state.web_scraper.execute_scraping(url, rules, max_pages)
                        if results:
                            # Display results
                            df = pd.DataFrame(results)
                            st.success("Scraping completed!")
                            st.dataframe(df)
                            
                            # Save results
                            st.session_state.latest_price_scraping = {
                                'url': url,
                                'timestamp': datetime.now().isoformat(),
                                'results': results,
                                'rules': rules
                            }
                            
                            # Download option
                            csv = df.to_csv(index=False)
                            st.download_button(
                                "Download Results (CSV)",
                                csv,
                                "price_scraping_results.csv",
                                "text/csv",
                                key='download-quick-csv'
                            )
                            
                            # Save rules option
                            if st.button("Save Rules for Future Use", key="save_quick_rules"):
                                st.session_state.saved_scraping_rules[url] = rules
                                st.success("Rules saved successfully!")

    with tab2:
        st.subheader("Advanced Price Scraping")
        
        # Model selection
        st.subheader("Select AI Model")
        models = st.session_state.web_scraper.get_available_models()
        
        model_provider = st.selectbox(
            "AI Provider",
            options=list(models.keys()),
            key="advanced_provider"
        )
        
        model_name = st.selectbox(
            "Model",
            options=models[model_provider],
            key="advanced_model"
        )

        # URL input
        url = st.text_input("URL to scrape", key="advanced_url")
        
        # Multi-page settings
        max_pages = st.number_input("Maximum pages to scrape", min_value=1, value=5, key="advanced_max_pages")

        # Fields to extract
        st.subheader("Fields to Extract:")
        if 'advanced_scraping_fields' not in st.session_state:
            st.session_state.advanced_scraping_fields = ["name", "price", "sku", "availability"]

        # Add new field
        col1, col2 = st.columns([3, 1])
        with col1:
            new_field = st.text_input("Add field", key="advanced_new_field")
        with col2:
            if st.button("Add Field", key="advanced_add"):
                if new_field and new_field not in st.session_state.advanced_scraping_fields:
                    st.session_state.advanced_scraping_fields.append(new_field)
                    st.rerun()

        # Display and manage fields
        st.write("Current fields:")
        for field in st.session_state.advanced_scraping_fields:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(field)
            with col2:
                if st.button("❌", key=f"advanced_remove_{field}"):
                    st.session_state.advanced_scraping_fields.remove(field)
                    st.rerun()

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            analyze_button = st.button("1. Analyze URL", key="advanced_analyze", use_container_width=True)
        with col2:
            generate_button = st.button("2. Generate Rules", key="advanced_generate", use_container_width=True)
        with col3:
            start_button = st.button("3. Start Scraping", key="advanced_start", type="primary", use_container_width=True)

        # Analyze URL
        if url and analyze_button:
            with st.spinner("Analyzing URL..."):
                analysis = asyncio.run(
                    st.session_state.web_scraper.analyze_url(
                        url,
                        model_provider,
                        model_name
                    )
                )
                if analysis and "suggested_fields" in analysis:
                    st.subheader("Suggested Fields")
                    for field in analysis["suggested_fields"]:
                        if st.button(
                            f"Add {field['name']} ({field['importance']})",
                            key=f"advanced_add_{field['name']}",
                            help=field['description']
                        ):
                            if field['name'] not in st.session_state.advanced_scraping_fields:
                                st.session_state.advanced_scraping_fields.append(field['name'])
                                st.rerun()

        # Generate scraping rules
        if url and st.session_state.advanced_scraping_fields and generate_button:
            with st.spinner("Generating scraping rules..."):
                rules = asyncio.run(
                    st.session_state.web_scraper.generate_scraping_rules(
                        url,
                        st.session_state.advanced_scraping_fields,
                        model_provider,
                        model_name
                    )
                )
                if rules and "selectors" in rules:
                    st.subheader("Generated Scraping Rules")
                    st.json(rules)
                    st.session_state.advanced_scraping_rules = rules
                    
                    # Save rules button
                    if st.button("Save Rules", key="save_advanced_rules"):
                        st.session_state.saved_scraping_rules[url] = rules
                        st.success("Rules saved successfully!")

        # Execute scraping
        if url and 'advanced_scraping_rules' in st.session_state and start_button:
            with st.spinner("Scraping data..."):
                results = st.session_state.web_scraper.execute_scraping(
                    url,
                    st.session_state.advanced_scraping_rules,
                    max_pages
                )
                if results:
                    st.success("Scraping completed!")
                    
                    # Convert results to DataFrame
                    df = pd.DataFrame(results)
                    
                    # Display results
                    st.subheader("Scraping Results")
                    st.dataframe(df)
                    
                    # Save results
                    st.session_state.latest_price_scraping = {
                        'url': url,
                        'timestamp': datetime.now().isoformat(),
                        'results': results,
                        'rules': st.session_state.advanced_scraping_rules
                    }
                    
                    # Download button
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "Download Results (CSV)",
                        csv,
                        "advanced_price_scraping_results.csv",
                        "text/csv",
                        key='download-advanced-csv'
                    )

    with tab3:
        st.subheader("Saved Scraping Rules")
        if st.session_state.saved_scraping_rules:
            for saved_url, rules in st.session_state.saved_scraping_rules.items():
                with st.expander(saved_url):
                    st.json(rules)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Use These Rules", key=f"use_{saved_url}"):
                            st.session_state.advanced_scraping_rules = rules
                            st.success("Rules loaded! Go to Advanced Scraping tab to use them.")
                    with col2:
                        if st.button("Delete Rules", key=f"delete_{saved_url}"):
                            del st.session_state.saved_scraping_rules[saved_url]
                            st.rerun()
        else:
            st.info("No saved rules yet. Save rules from Quick Scrape or Advanced Scraping to see them here.")

def render_price_matching():
    """Render price matching interface"""
    st.title("Price Matching")
    
    # Show latest scraping results if available
    if 'latest_price_scraping' in st.session_state:
        st.subheader("Latest Scraped Data")
        scraping = st.session_state.latest_price_scraping
        st.write(f"Source: {scraping['url']}")
        st.write(f"Scraped at: {scraping['timestamp']}")
        
        df = pd.DataFrame(scraping['results'])
        st.dataframe(df)
        
        # Match prices with catalog
        if st.button("Match Prices with Catalog"):
            with st.spinner("Matching prices..."):
                # TODO: Implement price matching logic
                st.info("Price matching functionality coming soon!")

def render_competitor_analysis():
    """Render competitor analysis interface"""
    st.title("Competitor Analysis")
    
    # Show saved scraping data
    if 'saved_scraping_rules' in st.session_state:
        st.subheader("Saved Competitor URLs")
        for url in st.session_state.saved_scraping_rules.keys():
            st.write(url)
            if st.button("Analyze", key=f"analyze_{url}"):
                # TODO: Implement competitor analysis logic
                st.info("Competitor analysis functionality coming soon!")
