from models.database import SessionLocal, ValidationRule, ImportHistory, ImportRuleExecution, ArchivedProduct, Catalog
from datetime import datetime, timedelta
import re
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd

class ValidationService:
    @staticmethod
    def get_all_rules() -> List[ValidationRule]:
        """Get all validation rules ordered by priority"""
        db = SessionLocal()
        try:
            return db.query(ValidationRule).order_by(ValidationRule.priority).all()
        finally:
            db.close()

    @staticmethod
    def add_rule(name: str, description: str, rule_type: str, condition: str, action: str, priority: int = 0) -> ValidationRule:
        """Add a new validation rule"""
        db = SessionLocal()
        try:
            rule = ValidationRule(
                name=name,
                description=description,
                rule_type=rule_type,
                condition=condition,
                action=action,
                priority=priority
            )
            db.add(rule)
            db.commit()
            return rule
        finally:
            db.close()

    @staticmethod
    def update_rule(rule_id: int, **kwargs) -> Tuple[bool, str]:
        """Update an existing validation rule"""
        db = SessionLocal()
        try:
            rule = db.query(ValidationRule).get(rule_id)
            if not rule:
                return False, "Rule not found"
            
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            db.commit()
            return True, "Rule updated successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error updating rule: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def validate_barcode(barcode: str) -> Tuple[bool, str]:
        """Validate a barcode according to rules"""
        if not barcode:
            return True, barcode

        # Remove any whitespace
        barcode = str(barcode).strip()

        # Check if barcode contains only numbers
        if not barcode.isdigit():
            return False, ""

        # Check for minimum length (e.g., EAN-13 should be 13 digits)
        if len(barcode) not in [8, 12, 13, 14]:
            return False, ""

        return True, barcode

    @staticmethod
    def check_duplicate_barcode(db, barcode: str) -> bool:
        """Check if barcode already exists"""
        if not barcode:
            return False
        count = db.query(Catalog).filter(Catalog.barcode == barcode).count()
        return count > 0

    @staticmethod
    def calculate_data_freshness(file_date: datetime) -> int:
        """Calculate data freshness in hours"""
        if not file_date:
            return 0
        
        # Calculate next day at same time
        next_day = file_date + timedelta(days=1)
        now = datetime.utcnow()
        
        # Calculate hours difference
        diff = now - file_date
        hours = int(diff.total_seconds() / 3600)
        
        return hours

    @staticmethod
    def archive_missing_products(db, current_products: List[str], source: str):
        """Archive products that are no longer in the import"""
        try:
            # Get existing products from this source
            existing_products = db.query(Catalog).filter(
                Catalog.source == source,
                Catalog.status == 'active'
            ).all()

            # Find products to archive
            for product in existing_products:
                if product.article_code not in current_products:
                    # Create archived product record
                    archived = ArchivedProduct(
                        original_id=product.id,
                        reference=product.reference,
                        article_code=product.article_code,
                        name=product.name,
                        barcode=product.barcode,
                        description=product.description,
                        price=product.price,
                        stock_quantity=product.stock_quantity,
                        purchase_price=product.purchase_price,
                        last_seen=product.updated_at,
                        archive_reason="missing from import",
                        source_data=product.data
                    )
                    db.add(archived)
                    
                    # Update original product status
                    product.status = 'archived'
                    
            db.commit()
            
        except Exception as e:
            db.rollback()
            logging.error(f"Error archiving products: {str(e)}")
            raise

    @staticmethod
    def process_import(df: pd.DataFrame, source: str, file_date: datetime) -> Tuple[bool, str, Dict]:
        """Process data import with validation rules"""
        db = SessionLocal()
        try:
            # Create import history record
            import_history = ValidationService.create_import_history(
                source=source,
                file_name="import_file",
                file_date=file_date
            )

            # Track statistics
            stats = {
                'total': len(df),
                'processed': 0,
                'errors': 0,
                'updated': 0,
                'created': 0,
                'archived': 0
            }

            # Get active rules
            rules = db.query(ValidationRule).filter(
                ValidationRule.is_active == True
            ).order_by(ValidationRule.priority).all()

            # Process each row
            current_products = []
            error_details = []

            for _, row in df.iterrows():
                try:
                    data = row.to_dict()
                    modified_data = data.copy()

                    # Apply validation rules
                    for rule in rules:
                        try:
                            if rule.rule_type == "barcode":
                                if "barcode" in modified_data:
                                    is_valid, new_barcode = ValidationService.validate_barcode(modified_data["barcode"])
                                    if not is_valid:
                                        modified_data["barcode"] = new_barcode

                            # Add more rule types here...
                            
                        except Exception as rule_error:
                            error_details.append(f"Rule '{rule.name}' error: {str(rule_error)}")

                    # Check for duplicate barcodes
                    if modified_data.get('barcode') and ValidationService.check_duplicate_barcode(db, modified_data['barcode']):
                        modified_data['barcode'] = ''  # Clear duplicate barcode

                    # Calculate data freshness
                    data_freshness = ValidationService.calculate_data_freshness(file_date)
                    modified_data['data_freshness'] = data_freshness
                    modified_data['data_timestamp'] = file_date
                    modified_data['import_timestamp'] = datetime.utcnow()

                    # Update or create product
                    existing_product = None
                    if modified_data.get('article_code'):
                        existing_product = db.query(Catalog).filter(
                            Catalog.article_code == modified_data['article_code']
                        ).first()

                    if existing_product:
                        # Update existing product
                        for key, value in modified_data.items():
                            setattr(existing_product, key, value)
                        existing_product.updated_at = datetime.utcnow()
                        stats['updated'] += 1
                    else:
                        # Create new product
                        new_product = Catalog(**modified_data)
                        db.add(new_product)
                        stats['created'] += 1

                    current_products.append(modified_data.get('article_code'))
                    stats['processed'] += 1

                except Exception as e:
                    stats['errors'] += 1
                    error_details.append(f"Row processing error: {str(e)}")

            # Archive missing products
            ValidationService.archive_missing_products(db, current_products, source)

            # Clean up old import history (keep last 5 days)
            cleanup_date = datetime.utcnow() - timedelta(days=5)
            db.query(ImportHistory).filter(
                ImportHistory.import_date < cleanup_date
            ).delete()

            # Update import history
            import_history.status = "completed"
            import_history.total_records = stats['total']
            import_history.processed_records = stats['processed']
            import_history.error_records = stats['errors']
            import_history.error_details = {'errors': error_details}
            import_history.import_metadata = stats

            db.commit()
            
            return True, "Import completed successfully", stats

        except Exception as e:
            db.rollback()
            logging.error(f"Import processing error: {str(e)}")
            return False, f"Import failed: {str(e)}", {}
        finally:
            db.close()

    @staticmethod
    def create_import_history(source: str, file_name: str, file_date: datetime) -> ImportHistory:
        """Create a new import history record"""
        db = SessionLocal()
        try:
            import_history = ImportHistory(
                source=source,
                file_name=file_name,
                file_date=file_date,
                status="started",
                total_records=0,
                processed_records=0,
                error_records=0,
                error_details={},
                rules_applied={},
                import_metadata={}
            )
            db.add(import_history)
            db.commit()
            return import_history
        finally:
            db.close()

    @staticmethod
    def get_import_history(days: int = 5) -> List[ImportHistory]:
        """Get import history for the specified number of days"""
        db = SessionLocal()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return db.query(ImportHistory).filter(
                ImportHistory.import_date >= start_date
            ).order_by(ImportHistory.import_date.desc()).all()
        finally:
            db.close()

    @staticmethod
    def get_archived_products(days: int = 5) -> List[ArchivedProduct]:
        """Get archived products for the specified number of days"""
        db = SessionLocal()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return db.query(ArchivedProduct).filter(
                ArchivedProduct.archived_at >= start_date
            ).order_by(ArchivedProduct.archived_at.desc()).all()
        finally:
            db.close()
