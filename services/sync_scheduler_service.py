from models.database import SessionLocal, PlatformConnection, SyncSchedule, SyncLog, SyncDirection, ScheduleFrequency
from datetime import datetime, timedelta
from services.file_handling_service import FileHandlingService
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

class SyncSchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.file_handler = FileHandlingService()
        self._load_schedules()

    def _load_schedules(self):
        """Load all active schedules from database and schedule them"""
        db = SessionLocal()
        try:
            schedules = db.query(SyncSchedule).filter(
                SyncSchedule.is_active == True
            ).all()
            
            for schedule in schedules:
                self._schedule_sync(schedule)
        finally:
            db.close()

    def _schedule_sync(self, schedule):
        """Schedule a sync based on its configuration"""
        if schedule.frequency == ScheduleFrequency.DAILY.value:
            hour, minute = schedule.time_of_day.split(':')
            trigger = CronTrigger(
                hour=int(hour),
                minute=int(minute)
            )
        elif schedule.frequency == ScheduleFrequency.WEEKLY.value:
            hour, minute = schedule.time_of_day.split(':')
            trigger = CronTrigger(
                day_of_week=schedule.day_of_week,
                hour=int(hour),
                minute=int(minute)
            )
        elif schedule.frequency == ScheduleFrequency.MONTHLY.value:
            hour, minute = schedule.time_of_day.split(':')
            trigger = CronTrigger(
                day=schedule.day_of_month,
                hour=int(hour),
                minute=int(minute)
            )
        else:  # HOURLY
            trigger = CronTrigger(minute=0)  # Every hour at minute 0

        self.scheduler.add_job(
            func=self._run_sync,
            trigger=trigger,
            args=[schedule.id],
            id=f'sync_{schedule.id}',
            replace_existing=True
        )

    def _run_sync(self, schedule_id):
        """Execute the sync operation"""
        db = SessionLocal()
        try:
            schedule = db.query(SyncSchedule).get(schedule_id)
            if not schedule or not schedule.is_active:
                return

            platform = schedule.platform
            if not platform or not platform.is_active:
                return

            # Create sync log entry
            sync_log = SyncLog(
                platform_id=platform.id,
                schedule_id=schedule_id,
                direction=platform.sync_direction,
                start_time=datetime.utcnow(),
                status="started"
            )
            db.add(sync_log)
            db.commit()

            try:
                # Perform sync based on platform type
                if platform.platform_type == "odoo":
                    self._sync_odoo(platform, sync_log)
                elif platform.platform_type == "prestashop":
                    self._sync_prestashop(platform, sync_log)
                elif platform.platform_type == "woocommerce":
                    self._sync_woocommerce(platform, sync_log)

                sync_log.status = "success"
                sync_log.end_time = datetime.utcnow()
                
                # Update next run time
                schedule.last_run = datetime.utcnow()
                schedule.next_run = self._calculate_next_run(schedule)
                
            except Exception as e:
                logging.error(f"Sync error: {str(e)}")
                sync_log.status = "failed"
                sync_log.end_time = datetime.utcnow()
                sync_log.error_details = {"error": str(e)}
                
            db.commit()

        finally:
            db.close()

    def _sync_odoo(self, platform, sync_log):
        """Perform Odoo sync with proper file handling"""
        from services.odoo_service import OdooService
        
        odoo_service = OdooService(
            url=platform.url,
            port=platform.port,
            db=platform.database,
            username=platform.username,
            password=platform.password
        )

        try:
            if platform.sync_direction == SyncDirection.IMPORT.value:
                # Get data from Odoo
                data = odoo_service.get_products()
                
                # Save to temporary file
                temp_file = "temp_odoo_import.csv"
                data.to_csv(temp_file, index=False, encoding='utf-8-sig')
                
                # Process with file handler
                df, encoding = self.file_handler.read_file_with_encoding(temp_file)
                df = self.file_handler.normalize_dataframe(df)
                
                # Archive the import file
                archive_path = self.file_handler.save_import_file(temp_file)
                
                # Get file date and update sync log
                file_date = self.file_handler.get_file_date(temp_file)
                sync_log.import_metadata = {
                    'file_date': file_date.isoformat(),
                    'encoding': encoding,
                    'archive_path': archive_path
                }
                
                # Process the data
                records = odoo_service.process_products(df)
                sync_log.records_processed = len(records)
                
            elif platform.sync_direction == SyncDirection.EXPORT.value:
                records = odoo_service.export_products()
                sync_log.records_processed = len(records)
                
            elif platform.sync_direction == SyncDirection.BIDIRECTIONAL.value:
                # Handle bidirectional sync
                imported = odoo_service.import_products()
                exported = odoo_service.export_products()
                sync_log.records_processed = len(imported) + len(exported)
                
        except Exception as e:
            logging.error(f"Odoo sync error: {str(e)}")
            raise

    def _sync_prestashop(self, platform, sync_log):
        """Perform PrestaShop sync"""
        # Implement PrestaShop sync logic
        pass

    def _sync_woocommerce(self, platform, sync_log):
        """Perform WooCommerce sync"""
        # Implement WooCommerce sync logic
        pass

    def _calculate_next_run(self, schedule):
        """Calculate the next run time based on schedule frequency"""
        now = datetime.utcnow()
        hour, minute = schedule.time_of_day.split(':')
        hour, minute = int(hour), int(minute)

        if schedule.frequency == ScheduleFrequency.HOURLY.value:
            return now + timedelta(hours=1)
        
        elif schedule.frequency == ScheduleFrequency.DAILY.value:
            next_run = now.replace(hour=hour, minute=minute)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        elif schedule.frequency == ScheduleFrequency.WEEKLY.value:
            days_ahead = schedule.day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_run = now + timedelta(days=days_ahead)
            return next_run.replace(hour=hour, minute=minute)
        
        elif schedule.frequency == ScheduleFrequency.MONTHLY.value:
            next_run = now.replace(day=schedule.day_of_month, hour=hour, minute=minute)
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
            return next_run
