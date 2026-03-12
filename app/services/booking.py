import logging
import uuid
from datetime import datetime, timezone

import resend

from app.config import get_settings

logger = logging.getLogger(__name__)

URGENCY_PT = {
    "emergency": "EMERGÊNCIA — Ir imediatamente às urgências",
    "urgent": "URGENTE — Consultar médico nos próximos dias",
    "routine": "ROTINA — Consulta regular",
}

URGENCY_COLOR = {
    "emergency": "#dc2626",
    "urgent": "#d97706",
    "routine": "#16a34a",
}

JITSI_BASE = "https://meet.jit.si"

MONTHS_PT = [
    "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def generate_video_room() -> str:
    room_id = uuid.uuid4().hex[:16]
    return f"{JITSI_BASE}/consultamedica-{room_id}"


def format_datetime_pt(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return f"{dt.day} de {MONTHS_PT[dt.month]} de {dt.year}, {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return iso_str


def _send_email(to: str, subject: str, html_body: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        logger.info("Resend not configured — email not sent to %s", to)
        return

    resend.api_key = settings.resend_api_key
    resend.Emails.send({
        "from": settings.sender_email,
        "to": [to],
        "subject": subject,
        "html": html_body,
    })


def _appointment_box_html(datetime_pt: str, video_url: str) -> str:
    return f"""
    <div style="background: #eff6ff; border: 2px solid #3b82f6; border-radius: 10px;
                padding: 16px; margin: 20px 0; text-align: center;">
      <p style="margin: 0 0 4px 0; font-size: 13px; color: #1e40af; font-weight: bold; text-transform: uppercase; letter-spacing: 0.05em;">
        Consulta agendada para
      </p>
      <p style="margin: 0 0 16px 0; font-size: 22px; font-weight: bold; color: #1e3a8a;">
        {datetime_pt}
      </p>
      <a href="{video_url}" target="_blank"
         style="background: #1e40af; color: white; padding: 12px 28px; border-radius: 8px;
                text-decoration: none; font-size: 15px; font-weight: bold; display: inline-block;">
        Entrar na videoconsulta
      </a>
      <p style="margin: 10px 0 0 0; font-size: 11px; color: #6b7280;">
        Link direto: <a href="{video_url}" style="color: #3b82f6;">{video_url}</a>
      </p>
    </div>
    """


def send_booking_to_doctor(
    name: str,
    email: str,
    phone: str,
    urgency: str,
    advice: str,
    patient_summary: str,
    video_url: str,
    slot_datetime: str,
) -> None:
    settings = get_settings()
    urgency_label = URGENCY_PT.get(urgency, urgency.upper())
    color = URGENCY_COLOR.get(urgency, "#333")
    datetime_pt = format_datetime_pt(slot_datetime)

    if not settings.doctor_email:
        logger.info(
            "BOOKING (no doctor_email configured): patient=%s | slot=%s | urgency=%s | video=%s",
            name, datetime_pt, urgency, video_url,
        )
        return

    subject = f"[ConsultaMedica.ai] Videoconsulta agendada — {name} — {datetime_pt}"

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 680px; margin: auto;">
      <h2 style="color: #1e40af;">Nova Videoconsulta Agendada</h2>

      <table style="border-collapse: collapse; width: 100%; border: 1px solid #e2e8f0; border-radius: 8px;">
        <tr style="background: #f8fafc;">
          <td style="padding: 8px 12px; font-weight: bold; width: 140px;">Paciente</td>
          <td style="padding: 8px 12px;">{name}</td>
        </tr>
        <tr>
          <td style="padding: 8px 12px; font-weight: bold;">Email</td>
          <td style="padding: 8px 12px;"><a href="mailto:{email}">{email}</a></td>
        </tr>
        <tr style="background: #f8fafc;">
          <td style="padding: 8px 12px; font-weight: bold;">Telefone</td>
          <td style="padding: 8px 12px;">{phone}</td>
        </tr>
        <tr>
          <td style="padding: 8px 12px; font-weight: bold;">Urgencia</td>
          <td style="padding: 8px 12px; color: {color}; font-weight: bold;">{urgency_label}</td>
        </tr>
      </table>

      {_appointment_box_html(datetime_pt, video_url)}

      <h3 style="margin-top: 24px; color: #1e40af;">Perfil clínico recolhido pela IA</h3>
      <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px;
                  white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{patient_summary}</div>

      <h3 style="margin-top: 24px; color: #1e40af;">Orientação gerada pela IA</h3>
      <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 12px;
                  white-space: pre-wrap; font-size: 14px; line-height: 1.6;">{advice}</div>

      <p style="margin-top: 24px; color: #6b7280; font-size: 12px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
        Gerado automaticamente pela plataforma ConsultaMedica.ai.
      </p>
    </body></html>
    """

    _send_email(settings.doctor_email, subject, html)
    logger.info("Booking email sent to doctor: patient=%s slot=%s room=%s", name, datetime_pt, video_url)


def send_confirmation_to_patient(
    name: str,
    email: str,
    urgency: str,
    video_url: str,
    slot_datetime: str,
) -> None:
    settings = get_settings()
    if not settings.resend_api_key or not email:
        return

    urgency_label = URGENCY_PT.get(urgency, urgency.upper())
    color = URGENCY_COLOR.get(urgency, "#333")
    datetime_pt = format_datetime_pt(slot_datetime)
    subject = f"[ConsultaMedica.ai] Videoconsulta confirmada — {datetime_pt}"

    html = f"""
    <html><body style="font-family: Arial, sans-serif; color: #333; max-width: 680px; margin: auto;">
      <h2 style="color: #1e40af;">Olá, {name}!</h2>
      <p>A sua videoconsulta foi agendada com sucesso.</p>

      {_appointment_box_html(datetime_pt, video_url)}

      <p><strong>Urgência avaliada pela IA:</strong>
        <span style="color: {color}; font-weight: bold;">{urgency_label}</span>
      </p>

      <div style="background: #fef9c3; border: 1px solid #fde68a; border-radius: 8px; padding: 12px; margin-top: 16px;">
        <p style="margin: 0; font-size: 13px; color: #854d0e;">
          <strong>Guarde este email.</strong> Na hora marcada, clique no botão "Entrar na videoconsulta".
          Não é necessário instalar nada — funciona directamente no browser.
          A sala ficará disponível assim que o médico entrar.
        </p>
      </div>

      <p style="margin-top: 24px; color: #6b7280; font-size: 12px; border-top: 1px solid #e2e8f0; padding-top: 12px;">
        ConsultaMedica.ai — Email automático, por favor não responda.
      </p>
    </body></html>
    """

    _send_email(email, subject, html)
    logger.info("Confirmation email sent to patient: %s slot=%s", email, datetime_pt)


def process_booking(
    name: str,
    email: str,
    phone: str,
    urgency: str,
    advice: str,
    patient_summary: str,
    slot_datetime: str,
) -> str:
    """Generate video room, send emails, return video_url."""
    video_url = generate_video_room()

    send_booking_to_doctor(
        name=name,
        email=email,
        phone=phone,
        urgency=urgency,
        advice=advice,
        patient_summary=patient_summary,
        video_url=video_url,
        slot_datetime=slot_datetime,
    )
    send_confirmation_to_patient(
        name=name,
        email=email,
        urgency=urgency,
        video_url=video_url,
        slot_datetime=slot_datetime,
    )

    return video_url
