import streamlit as st
from services.subscription_service import SubscriptionService
import pandas as pd
from datetime import datetime
from models.database import SessionLocal
from sqlalchemy import or_
from models.subscription_models import User, Subscription, Payment

class SubscriptionManager:
    def __init__(self, db):
        self.db = db
        if 'subscription_service' not in st.session_state:
            st.session_state.subscription_service = SubscriptionService()
    
    def render(self):
        """Render subscription management interface"""
        st.title("Subscription Management")

        # Tabs for different subscription management views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Overview", 
            "Plan Management", 
            "User Subscriptions",
            "Revenue Analytics",
            "Payment Settings"
        ])

        with tab1:
            self.render_overview()

        with tab2:
            self.render_plan_management()

        with tab3:
            self.render_user_subscriptions()

        with tab4:
            self.render_revenue_analytics()

        with tab5:
            self.render_payment_settings()

    def render_overview(self):
        """Render subscription overview"""
        metrics = st.session_state.subscription_service.get_subscription_metrics()
        
        # Display metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Total Users",
                value=metrics['total_users']
            )
        
        with col2:
            st.metric(
                label="Active Subscriptions",
                value=metrics['active_subscriptions']
            )
        
        with col3:
            st.metric(
                label="Trial Users",
                value=metrics['trial_users']
            )
        
        with col4:
            st.metric(
                label="Monthly Revenue",
                value=f"€{metrics['monthly_revenue'].get('EUR', 0):,.2f}"
            )

        # Recent activity
        st.subheader("Recent Activity")
        if 'audit_logs' in metrics:
            df = pd.DataFrame(metrics['audit_logs'])
            st.dataframe(df)

    def render_plan_management(self):
        """Render plan management interface"""
        st.subheader("Plan Configuration")
        
        # Get current plans
        plans = st.session_state.subscription_service.plans
        
        for plan_type, plan in plans.items():
            st.write(f"### {plan_type.title()}")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_limit = st.number_input(
                    "Product Limit",
                    min_value=100,
                    value=plan['product_limit'],
                    key=f"limit_{plan_type}"
                )
            
            with col2:
                new_price = st.number_input(
                    "Price (€)",
                    min_value=0.0,
                    value=float(plan['price']),
                    key=f"price_{plan_type}"
                )
            
            with col3:
                if st.button("Update", key=f"update_{plan_type}"):
                    success = st.session_state.subscription_service.update_plan_limits(
                        plan_type,
                        new_limit,
                        new_price
                    )
                    if success:
                        st.success(f"{plan_type.title()} plan updated successfully!")
                    else:
                        st.error("Failed to update plan")

    def render_user_subscriptions(self):
        """Render user subscription management"""
        st.subheader("User Subscriptions")
        
        # Search users
        search = st.text_input("Search by email or username")
        
        # Get subscriptions
        try:
            query = self.db.query(User, Subscription).join(Subscription)
            if search:
                query = query.filter(
                    or_(
                        User.email.ilike(f"%{search}%"),
                        User.username.ilike(f"%{search}%")
                    )
                )
            
            results = query.all()
            
            # Display subscriptions
            for user, subscription in results:
                with st.expander(f"{user.email} - {subscription.plan_type}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**User Details**")
                        st.write(f"Username: {user.username}")
                        st.write(f"Created: {user.created_at}")
                        st.write(f"Products: {user.catalog_count}")
                    
                    with col2:
                        st.write("**Subscription Details**")
                        st.write(f"Status: {subscription.status}")
                        st.write(f"Started: {subscription.current_period_start}")
                        st.write(f"Expires: {subscription.current_period_end}")
                    
                    # Actions
                    if st.button("Cancel Subscription", key=f"cancel_{user.id}"):
                        if st.session_state.subscription_service.stripe_enabled:
                            success = st.session_state.subscription_service.cancel_subscription(
                                subscription.stripe_subscription_id
                            )
                            if success:
                                st.success("Subscription cancelled successfully!")
                            else:
                                st.error("Failed to cancel subscription")
                        else:
                            st.warning("Stripe is not configured. Please set up payment settings first.")
        except Exception as e:
            st.error(f"Error loading subscriptions: {str(e)}")

    def render_revenue_analytics(self):
        """Render revenue analytics"""
        st.subheader("Revenue Analytics")
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        if start_date and end_date:
            try:
                payments = self.db.query(Payment).filter(
                    Payment.paid_at.between(start_date, end_date)
                ).all()
                
                if payments:
                    # Create DataFrame
                    df = pd.DataFrame([
                        {
                            'date': p.paid_at.date(),
                            'amount': p.amount,
                            'currency': p.currency
                        }
                        for p in payments
                    ])
                    
                    # Group by date
                    daily_revenue = df.groupby('date')['amount'].sum().reset_index()
                    
                    # Plot revenue
                    st.line_chart(daily_revenue.set_index('date'))
                    
                    # Summary statistics
                    st.write("### Summary")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Total Revenue",
                            f"€{df['amount'].sum():,.2f}"
                        )
                    
                    with col2:
                        st.metric(
                            "Average Daily Revenue",
                            f"€{df.groupby('date')['amount'].sum().mean():,.2f}"
                        )
                    
                    with col3:
                        st.metric(
                            "Number of Payments",
                            len(df)
                        )
                else:
                    st.info("No payment data found for the selected date range")
            except Exception as e:
                st.error(f"Error loading revenue data: {str(e)}")

    def render_payment_settings(self):
        """Render payment settings configuration"""
        st.subheader("Payment Settings")
        
        # Stripe configuration
        st.write("### Stripe Configuration")
        
        # Check current Stripe status
        stripe_status = "Enabled" if st.session_state.subscription_service.stripe_enabled else "Disabled"
        st.write(f"Current Status: **{stripe_status}**")
        
        # Stripe API key
        stripe_key = st.text_input(
            "Stripe Secret Key",
            type="password",
            value=st.secrets.get("STRIPE_SECRET_KEY", "")
        )
        
        if stripe_key:
            if st.button("Configure Stripe"):
                success, message = st.session_state.subscription_service.configure_stripe(stripe_key)
                if success:
                    st.success(message)
                    # Save to secrets
                    st.secrets["STRIPE_SECRET_KEY"] = stripe_key
                else:
                    st.error(message)
        
        # Stripe price IDs (only if Stripe is enabled)
        if st.session_state.subscription_service.stripe_enabled:
            st.write("### Stripe Price IDs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                basic_price_id = st.text_input(
                    "Basic Plan Price ID",
                    value=st.session_state.subscription_service.plans['basic'].get('stripe_price_id', '')
                )
            
            with col2:
                premium_price_id = st.text_input(
                    "Premium Plan Price ID",
                    value=st.session_state.subscription_service.plans['premium'].get('stripe_price_id', '')
                )
            
            if st.button("Save Price IDs"):
                success = st.session_state.subscription_service.configure_stripe_prices(
                    basic_price_id,
                    premium_price_id
                )
                if success:
                    st.success("Price IDs updated successfully!")
                else:
                    st.error("Failed to update price IDs")
