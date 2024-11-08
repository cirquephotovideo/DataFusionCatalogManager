import streamlit as st
import pandas as pd
from typing import List, Optional
from datetime import datetime
from models.database import SessionLocal, User, Subscription, Payment
from sqlalchemy import or_

class SubscriptionManager:
    def __init__(self, db):
        self.db = db

    def render(self):
        st.header("Subscription Management")
        
        # Add tabs for different sections
        tab1, tab2, tab3 = st.tabs(["Active Subscriptions", "Add Subscription", "Subscription History"])
        
        with tab1:
            self.render_active_subscriptions()
        
        with tab2:
            self.render_add_subscription()
        
        with tab3:
            self.render_subscription_history()

    def render_active_subscriptions(self):
        st.subheader("Active Subscriptions")
        
        # Get active subscriptions
        active_subs = self.get_active_subscriptions()
        
        if active_subs:
            for sub in active_subs:
                with st.expander(f"{sub.user.email} - {sub.plan_type}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Start Date:**", sub.start_date.strftime("%Y-%m-%d"))
                        st.write("**End Date:**", sub.end_date.strftime("%Y-%m-%d"))
                        st.write("**Status:**", sub.status)
                    with col2:
                        # Show recent payments
                        if sub.payments:
                            st.write("**Recent Payment:**")
                            latest_payment = sorted(sub.payments, key=lambda x: x.created_at)[-1]
                            st.write(f"Amount: ${latest_payment.amount:.2f}")
                            st.write(f"Date: {latest_payment.created_at.strftime('%Y-%m-%d')}")
                    
                    # Add action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Renew", key=f"renew_{sub.id}"):
                            self.renew_subscription(sub.id)
                            st.success("Subscription renewed!")
                    with col2:
                        if st.button("Cancel", key=f"cancel_{sub.id}"):
                            self.cancel_subscription(sub.id)
                            st.success("Subscription cancelled!")
        else:
            st.info("No active subscriptions found")

    def render_add_subscription(self):
        st.subheader("Add New Subscription")
        
        with st.form("new_subscription"):
            # User information
            email = st.text_input("Email")
            username = st.text_input("Username")
            
            # Subscription details
            plan_type = st.selectbox("Plan Type", ["Basic", "Premium", "Enterprise"])
            duration_months = st.number_input("Duration (months)", min_value=1, max_value=12, value=1)
            
            # Payment information
            amount = st.number_input("Payment Amount", min_value=0.0, value=0.0)
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP"])
            payment_method = st.selectbox("Payment Method", ["Credit Card", "PayPal", "Bank Transfer"])
            
            if st.form_submit_button("Create Subscription"):
                success = self.create_subscription(
                    email=email,
                    username=username,
                    plan_type=plan_type,
                    duration_months=duration_months,
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method
                )
                
                if success:
                    st.success("Subscription created successfully!")
                else:
                    st.error("Error creating subscription")

    def render_subscription_history(self):
        st.subheader("Subscription History")
        
        # Search box
        search_query = st.text_input("Search by email or username")
        
        if search_query:
            history = self.search_subscription_history(search_query)
            
            if history:
                for sub in history:
                    with st.expander(f"{sub.user.email} - {sub.plan_type}"):
                        st.write("**Status:**", sub.status)
                        st.write("**Period:**", f"{sub.start_date.strftime('%Y-%m-%d')} to {sub.end_date.strftime('%Y-%m-%d')}")
                        
                        if sub.payments:
                            st.write("**Payment History:**")
                            payment_data = []
                            for payment in sorted(sub.payments, key=lambda x: x.created_at, reverse=True):
                                payment_data.append({
                                    "Date": payment.created_at.strftime("%Y-%m-%d"),
                                    "Amount": f"${payment.amount:.2f}",
                                    "Method": payment.payment_method,
                                    "Status": payment.status
                                })
                            st.table(pd.DataFrame(payment_data))
            else:
                st.info("No subscription history found")

    def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions"""
        return (
            self.db.query(Subscription)
            .filter(Subscription.status == "active")
            .all()
        )

    def search_subscription_history(self, query: str) -> List[Subscription]:
        """Search subscription history by email or username"""
        return (
            self.db.query(Subscription)
            .join(User)
            .filter(
                or_(
                    User.email.ilike(f"%{query}%"),
                    User.username.ilike(f"%{query}%")
                )
            )
            .all()
        )

    def create_subscription(
        self,
        email: str,
        username: str,
        plan_type: str,
        duration_months: int,
        amount: float,
        currency: str,
        payment_method: str
    ) -> bool:
        """Create a new subscription with initial payment"""
        try:
            # Create or get user
            user = (
                self.db.query(User)
                .filter(User.email == email)
                .first()
            )
            
            if not user:
                user = User(
                    email=email,
                    username=username
                )
                self.db.add(user)
                self.db.flush()
            
            # Create subscription
            start_date = datetime.utcnow()
            end_date = datetime(
                year=start_date.year + ((start_date.month + duration_months - 1) // 12),
                month=((start_date.month + duration_months - 1) % 12) + 1,
                day=start_date.day
            )
            
            subscription = Subscription(
                user_id=user.id,
                plan_type=plan_type,
                start_date=start_date,
                end_date=end_date,
                status="active"
            )
            self.db.add(subscription)
            self.db.flush()
            
            # Create initial payment
            payment = Payment(
                user_id=user.id,
                subscription_id=subscription.id,
                amount=amount,
                currency=currency,
                status="success",
                payment_method=payment_method,
                transaction_id=f"TRANS_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            )
            self.db.add(payment)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            st.error(f"Error: {str(e)}")
            return False

    def renew_subscription(self, subscription_id: int) -> bool:
        """Renew an existing subscription"""
        try:
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.id == subscription_id)
                .first()
            )
            
            if subscription:
                # Extend end date by 1 month
                current_end = subscription.end_date
                new_end = datetime(
                    year=current_end.year + ((current_end.month) // 12),
                    month=((current_end.month) % 12) + 1,
                    day=current_end.day
                )
                subscription.end_date = new_end
                subscription.status = "active"
                
                self.db.commit()
                return True
                
        except Exception as e:
            self.db.rollback()
            st.error(f"Error: {str(e)}")
            return False

    def cancel_subscription(self, subscription_id: int) -> bool:
        """Cancel an existing subscription"""
        try:
            subscription = (
                self.db.query(Subscription)
                .filter(Subscription.id == subscription_id)
                .first()
            )
            
            if subscription:
                subscription.status = "cancelled"
                self.db.commit()
                return True
                
        except Exception as e:
            self.db.rollback()
            st.error(f"Error: {str(e)}")
            return False
