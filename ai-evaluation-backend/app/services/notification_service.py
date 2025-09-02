import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from ..config import settings
from ..database import get_database
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.email_user = settings.email_user
        self.email_password = settings.email_password
        self.enabled = bool(self.email_user and self.email_password)
        
        if not self.enabled:
            logger.warning("Email notifications disabled - SMTP credentials not configured")
    
    async def send_batch_completion_notification(
        self, 
        session_id: str, 
        processed_count: int, 
        failed_count: int, 
        total_count: int
    ):
        """Send notification when batch processing completes."""
        try:
            if not self.enabled:
                logger.info("Skipping email notification - not configured")
                return
            
            db = get_database()
            
            # Get session and professor details
            session = await db.exam_sessions.find_one({"_id": ObjectId(session_id)})
            if not session:
                logger.error(f"Session {session_id} not found for notification")
                return
            
            professor = await db.users.find_one({"_id": session["professor_id"]})
            if not professor:
                logger.error(f"Professor not found for session {session_id}")
                return
            
            # Calculate success rate
            success_rate = (processed_count / total_count * 100) if total_count > 0 else 0
            
            # Create email content
            subject = f"Evaluation Complete: {session['session_name']}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Evaluation Processing Complete</h2>
                
                <p>Dear {professor['full_name']},</p>
                
                <p>The automatic evaluation of answer sheets for "<strong>{session['session_name']}</strong>" has been completed.</p>
                
                <h3>Processing Summary:</h3>
                <ul>
                    <li><strong>Total Scripts:</strong> {total_count}</li>
                    <li><strong>Successfully Processed:</strong> {processed_count}</li>
                    <li><strong>Failed:</strong> {failed_count}</li>
                    <li><strong>Success Rate:</strong> {success_rate:.1f}%</li>
                </ul>
                
                <p>You can now review the results and handle any scripts that require manual review.</p>
                
                <p><a href="http://localhost:3000">View Results</a></p>
                
                <p>Best regards,<br>
                AI Evaluation System</p>
            </body>
            </html>
            """
            
            text_content = f"""
            Evaluation Processing Complete
            
            Dear {professor['full_name']},
            
            The automatic evaluation of answer sheets for "{session['session_name']}" has been completed.
            
            Processing Summary:
            - Total Scripts: {total_count}
            - Successfully Processed: {processed_count}
            - Failed: {failed_count}
            - Success Rate: {success_rate:.1f}%
            
            You can now review the results and handle any scripts that require manual review.
            
            Best regards,
            AI Evaluation System
            """
            
            await self._send_email(
                to_email=professor['email'],
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(f"Batch completion notification sent to {professor['email']}")
            
        except Exception as e:
            logger.error(f"Error sending batch completion notification: {e}")
    
    async def send_manual_review_notification(
        self, 
        professor_email: str, 
        session_name: str, 
        student_name: str,
        review_reason: str
    ):
        """Send notification when a script requires manual review."""
        try:
            if not self.enabled:
                return
            
            subject = f"Manual Review Required: {session_name}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Manual Review Required</h2>
                
                <p>A script requires your manual review:</p>
                
                <ul>
                    <li><strong>Session:</strong> {session_name}</li>
                    <li><strong>Student:</strong> {student_name}</li>
                    <li><strong>Reason:</strong> {review_reason}</li>
                </ul>
                
                <p><a href="http://localhost:3000">Review Now</a></p>
                
                <p>Best regards,<br>
                AI Evaluation System</p>
            </body>
            </html>
            """
            
            text_content = f"""
            Manual Review Required
            
            A script requires your manual review:
            
            - Session: {session_name}
            - Student: {student_name}
            - Reason: {review_reason}
            
            Please log in to the system to review this script.
            
            Best regards,
            AI Evaluation System
            """
            
            await self._send_email(
                to_email=professor_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(f"Manual review notification sent to {professor_email}")
            
        except Exception as e:
            logger.error(f"Error sending manual review notification: {e}")
    
    async def send_processing_error_notification(
        self, 
        professor_email: str, 
        session_name: str, 
        error_details: str
    ):
        """Send notification when processing encounters errors."""
        try:
            if not self.enabled:
                return
            
            subject = f"Processing Error: {session_name}"
            
            html_content = f"""
            <html>
            <body>
                <h2>Processing Error</h2>
                
                <p>An error occurred while processing scripts for "{session_name}":</p>
                
                <p><strong>Error Details:</strong><br>
                {error_details}</p>
                
                <p>Please check the system logs or contact support for assistance.</p>
                
                <p><a href="http://localhost:3000">View Session</a></p>
                
                <p>Best regards,<br>
                AI Evaluation System</p>
            </body>
            </html>
            """
            
            text_content = f"""
            Processing Error
            
            An error occurred while processing scripts for "{session_name}":
            
            Error Details:
            {error_details}
            
            Please check the system logs or contact support for assistance.
            
            Best regards,
            AI Evaluation System
            """
            
            await self._send_email(
                to_email=professor_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(f"Processing error notification sent to {professor_email}")
            
        except Exception as e:
            logger.error(f"Error sending processing error notification: {e}")
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str, 
        text_content: str
    ):
        """Send an email using SMTP."""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_email
            
            # Add text and HTML parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.email_user,
                password=self.email_password
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            raise
    
    async def send_welcome_email(self, user_email: str, user_name: str):
        """Send welcome email to new users."""
        try:
            if not self.enabled:
                return
            
            subject = "Welcome to AI Evaluation System"
            
            html_content = f"""
            <html>
            <body>
                <h2>Welcome to AI Evaluation System!</h2>
                
                <p>Dear {user_name},</p>
                
                <p>Welcome to the AI-powered Answer Sheet Evaluation System. Your account has been created successfully.</p>
                
                <h3>Getting Started:</h3>
                <ol>
                    <li>Create your first evaluation scheme</li>
                    <li>Upload scheme documents (PDF)</li>
                    <li>Start a new exam session</li>
                    <li>Upload answer sheets for automatic evaluation</li>
                </ol>
                
                <p><a href="http://localhost:3000">Login to System</a></p>
                
                <p>If you have any questions, please don't hesitate to contact support.</p>
                
                <p>Best regards,<br>
                AI Evaluation System Team</p>
            </body>
            </html>
            """
            
            text_content = f"""
            Welcome to AI Evaluation System!
            
            Dear {user_name},
            
            Welcome to the AI-powered Answer Sheet Evaluation System. Your account has been created successfully.
            
            Getting Started:
            1. Create your first evaluation scheme
            2. Upload scheme documents (PDF)
            3. Start a new exam session
            4. Upload answer sheets for automatic evaluation
            
            If you have any questions, please don't hesitate to contact support.
            
            Best regards,
            AI Evaluation System Team
            """
            
            await self._send_email(
                to_email=user_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
            logger.info(f"Welcome email sent to {user_email}")
            
        except Exception as e:
            logger.error(f"Error sending welcome email: {e}")
    
    def test_email_configuration(self) -> bool:
        """Test if email configuration is working."""
        return self.enabled and all([
            self.smtp_server,
            self.smtp_port,
            self.email_user,
            self.email_password
        ])