from typing import Dict, List, Optional, Tuple
from models.database import SessionLocal, User, Subscription, Payment
from datetime import datetime, timedelta
import json
from sqlalchemy import func

class SubscriptionService:
    def __init__(self, stripe_key: Optional[str] = None):
        """Initialize subscription service"""
        self.stripe_enabled = False
        self.stripe = None
        if stripe_key:
            try:
                import stripe
                stripe.api_key = stripe_key
                self.stripe = stripe
                self.stripe_enabled = True
            except ImportError:
                print("Stripe module not available. Payment processing disabled.")
        
        self.plans = {
            'free_trial': {
                'name': 'Free Trial',
                'duration_days': 10,
                'product_limit': 5000,
                'price': 0
            },
            'basic': {
                'name': 'Basic',
                'product_limit': 5000,
                'price': 500,
                'stripe_price_id': ''  # Set this from admin interface
            },
            'premium': {
                'name': 'Premium',
                'product_limit': 10000,
                'price': 1000,
                'stripe_price_id': ''  # Set this from admin interface
            }
        }

    def configure_stripe(self, api_key: str) -> Tuple[bool, str]:
        """Configure Stripe integration"""
        try:
            import stripe
            stripe.api_key = api_key
            self.stripe = stripe
            self.stripe_enabled = True
            
            # Test the configuration
            stripe.PaymentMethod.list(limit=1)
            return True, "Stripe configured successfully"
        except ImportError:
            return False, "Stripe module not available"
        except Exception as e:
            self.stripe_enabled = False
            return False, f"Error configuring Stripe: {str(e)}"

    def create_customer(self, user_id: int, email: str) -> Optional[str]:
        """Create a Stripe customer if Stripe is enabled"""
        if not self.stripe_enabled:
            return None
            
        try:
            customer = self.stripe.Customer.create(
                email=email,
                metadata={'user_id': user_id}
            )
            return customer.id
        except Exception as e:
            print(f"Error creating customer: {str(e)}")
            return None

    def create_subscription(self, customer_id: str, price_id: str) -> Optional[Dict]:
        """Create a Stripe subscription if Stripe is enabled"""
        if not self.stripe_enabled:
            return None
            
        try:
            subscription = self.stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            return {
                'subscriptionId': subscription.id,
                'clientSecret': subscription.latest_invoice.payment_intent.client_secret
            }
        except Exception as e:
            print(f"Error creating subscription: {str(e)}")
            return None

    def start_free_trial(self, user_id: int) -> bool:
        """Start a free trial subscription"""
        db = SessionLocal()
        try:
            # Check if user already had a trial
            existing_trial = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.plan_type == 'free_trial'
            ).first()
            
            if existing_trial:
                return False
            
            # Create trial subscription
            trial_end = datetime.now() + timedelta(days=10)
            subscription = Subscription(
                user_id=user_id,
                plan_type='free_trial',
                status='trialing',
                current_period_start=datetime.now(),
                current_period_end=trial_end
            )
            db.add(subscription)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error starting trial: {str(e)}")
            return False
        finally:
            db.close()

    def check_subscription_access(self, user_id: int) -> Dict:
        """Check if user has active subscription"""
        db = SessionLocal()
        try:
            subscription = db.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status.in_(['active', 'trialing'])
            ).first()
            
            if not subscription:
                return {
                    'has_access': False,
                    'reason': 'No active subscription'
                }
            
            # Check product limit
            catalog_count = db.query(User).filter(
                User.id == user_id
            ).first().catalog_count
            
            plan = self.plans[subscription.plan_type]
            if catalog_count > plan['product_limit']:
                return {
                    'has_access': False,
                    'reason': 'Product limit exceeded'
                }
            
            return {
                'has_access': True,
                'plan': subscription.plan_type,
                'product_limit': plan['product_limit'],
                'product_count': catalog_count,
                'expires_at': subscription.current_period_end.isoformat()
            }
        finally:
            db.close()

    def get_subscription_metrics(self) -> Dict:
        """Get subscription metrics for admin dashboard"""
        db = SessionLocal()
        try:
            total_users = db.query(User).count()
            active_subscriptions = db.query(Subscription).filter(
                Subscription.status == 'active'
            ).count()
            trial_users = db.query(Subscription).filter(
                Subscription.status == 'trialing'
            ).count()
            
            # Revenue metrics
            current_month = datetime.now().replace(day=1)
            monthly_revenue = db.query(
                Payment.currency,
                func.sum(Payment.amount).label('total')
            ).filter(
                Payment.paid_at >= current_month
            ).group_by(Payment.currency).all()
            
            return {
                'total_users': total_users,
                'active_subscriptions': active_subscriptions,
                'trial_users': trial_users,
                'monthly_revenue': {
                    currency: float(amount) for currency, amount in monthly_revenue
                }
            }
        finally:
            db.close()

    def update_plan_limits(self, plan_type: str, product_limit: int, price: float) -> bool:
        """Update plan limits"""
        try:
            if plan_type not in self.plans:
                return False
            
            self.plans[plan_type]['product_limit'] = product_limit
            self.plans[plan_type]['price'] = price
            
            # Save updated plans to configuration
            with open('subscription_config.json', 'w') as f:
                json.dump(self.plans, f)
            
            return True
        except Exception as e:
            print(f"Error updating plan limits: {str(e)}")
            return False

    def configure_stripe_prices(self, basic_price_id: str, premium_price_id: str) -> bool:
        """Configure Stripe price IDs"""
        try:
            self.plans['basic']['stripe_price_id'] = basic_price_id
            self.plans['premium']['stripe_price_id'] = premium_price_id
            
            # Save updated plans to configuration
            with open('subscription_config.json', 'w') as f:
                json.dump(self.plans, f)
            
            return True
        except Exception as e:
            print(f"Error configuring Stripe prices: {str(e)}")
            return False
