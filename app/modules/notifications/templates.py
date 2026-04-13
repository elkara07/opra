"""Notification email templates."""

from __future__ import annotations


def ticket_created_template(ticket_number: str, subject: str, priority: str,
                            sla_response_hours: int | None = None) -> tuple[str, str]:
    """Generate email subject and HTML body for ticket creation notification.

    Returns (subject, body_html).
    """
    sla_text = ""
    if sla_response_hours:
        sla_text = f"<p>Our team will respond within <strong>{sla_response_hours} hours</strong>.</p>"

    email_subject = f"Re: {subject} [{ticket_number}]"
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <h2>Your request has been received</h2>
        <p>Thank you for contacting us. A support ticket has been created for your request.</p>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Ticket Number</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ticket_number}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Subject</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{subject}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Priority</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{priority}</td>
            </tr>
        </table>
        {sla_text}
        <p>To add information to this ticket, simply reply to this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 24px 0;">
        <p style="color: #888; font-size: 12px;">This is an automated message. Please do not remove the ticket number [{ticket_number}] from the subject line.</p>
    </div>
    """
    return email_subject, body


def escalation_template(ticket_number: str, subject: str, priority: str,
                        old_level: int, new_level: int, elapsed_minutes: int) -> tuple[str, str]:
    """Generate escalation notification email."""
    level_names = {1: "L1 Support", 2: "L2 Technical", 3: "L3 Expert", 4: "Management"}
    hours = elapsed_minutes // 60
    mins = elapsed_minutes % 60

    email_subject = f"[ESCALATION L{new_level}] {subject} [{ticket_number}]"
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 12px; border-radius: 4px;">
            <strong>Ticket Escalated</strong> — {ticket_number} has been escalated to {level_names.get(new_level, f'Level {new_level}')}.
        </div>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Ticket</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ticket_number}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Subject</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{subject}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Priority</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{priority}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Elapsed Time</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{hours}h {mins}m</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Escalation</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{level_names.get(old_level, f'L{old_level}')} → {level_names.get(new_level, f'L{new_level}')}</td>
            </tr>
        </table>
        <p>Please review and take action on this ticket promptly.</p>
    </div>
    """
    return email_subject, body


def sla_breach_template(ticket_number: str, subject: str, priority: str,
                        sla_type: str) -> tuple[str, str]:
    """Generate SLA breach notification email."""
    email_subject = f"[SLA BREACH] {sla_type.title()} SLA breached — {ticket_number}"
    body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px;">
        <div style="background: #f8d7da; border: 1px solid #dc3545; padding: 12px; border-radius: 4px;">
            <strong>SLA Breach Alert</strong> — The {sla_type} SLA for {ticket_number} has been breached.
        </div>
        <table style="border-collapse: collapse; width: 100%; margin: 16px 0;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Ticket</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{ticket_number}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Subject</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{subject}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Priority</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{priority}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">Breached SLA</td>
                <td style="padding: 8px; border: 1px solid #ddd; color: #dc3545; font-weight: bold;">{sla_type.title()} Time</td>
            </tr>
        </table>
        <p>Immediate attention is required.</p>
    </div>
    """
    return email_subject, body
