# TODO for Fixing Login Server Error

- [x] Check Database Migrations: Run showmigrations and migrate for users app
- [x] Verify Database Connection: Ensure MySQL is running or switch to SQLite
- [x] Add Error Handling in Login View: Wrap operations in try-except in users/views.py
- [x] Test Email Sending: Send a test email to verify SMTP
- [x] Run Server and Test Login: Start server, attempt login, check logs
- [x] Fix Identified Issues: Update settings or code based on errors

# TODO for Fixing Upload Server Error

- [x] Install missing dependencies: pytz for view_predictions
- [x] Fix model loading errors in core/views.py
- [x] Test upload and view_predictions after fixes (Server restarted, fixes applied)
