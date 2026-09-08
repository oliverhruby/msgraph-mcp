"""Email (Outlook) — messages, folders, drafts, attachments, rules, mailbox settings."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("mail", "GET", "/me/messages", delegated=["Mail.Read"])
def list_messages(
    top: int = None,
    filter: str = None,
    select: str = None,
    order_by: str = None,
    search: str = None,
):
    def go():
        params = to_query(**{
            "$top": top,
            "$filter": filter,
            "$select": select,
            "$orderby": order_by,
            "$search": search,
        })
        return run_sync(graph().get_all("/me/messages", params=params))
    return go()


@graph_tool("mail", "GET", "/me/messages/{id}", delegated=["Mail.Read"])
def get_message(message_id: str, select: str = None):
    def go():
        params = to_query(**{"$select": select})
        return run_sync(graph().get(f"/me/messages/{message_id}", params=params))
    return go()


@graph_tool("mail", "GET", "/me/messages/{id}/attachments", delegated=["Mail.Read"])
def list_attachments(message_id: str):
    def go():
        return run_sync(graph().get_all(f"/me/messages/{message_id}/attachments"))
    return go()


@graph_tool("mail", "GET", "/me/messages/{id}/attachments/{id}/$value", delegated=["Mail.Read"])
def download_attachment(message_id: str, attachment_id: str):
    """Get attachment content (returns base64-encoded bytes)."""
    def go():
        return run_sync(graph().get(f"/me/messages/{message_id}/attachments/{attachment_id}/$value"))
    return go()


@graph_tool("mail", "GET", "/me/mailFolders", delegated=["Mail.Read"])
def list_mail_folders(top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all("/me/mailFolders", params=params))
    return go()


@graph_tool("mail", "GET", "/me/mailFolders/{id}/messages", delegated=["Mail.Read"])
def list_folder_messages(folder_id: str, top: int = None, filter: str = None):
    def go():
        params = to_query(**{"$top": top, "$filter": filter})
        return run_sync(graph().get_all(f"/me/mailFolders/{folder_id}/messages", params=params))
    return go()


@graph_tool("mail", "GET", "/me/mailFolders/inbox/messageRules", delegated=["Mail.ReadWrite"])
def list_inbox_rules():
    def go():
        return run_sync(graph().get_all("/me/mailFolders/inbox/messageRules"))
    return go()


@graph_tool("mail", "POST", "/me/sendMail", delegated=["Mail.Send"])
def send_mail(
    to_recipients: str,
    subject: str,
    body: str,
    body_type: str = "HTML",
    cc_recipients: str = None,
    importance: str = None,
):
    """Send email. to_recipients/cc_recipients: semicolon-separated email addresses."""
    def go():
        require_write()
        to_list = [{"emailAddress": {"address": a.strip()}} for a in to_recipients.split(";")]
        payload: dict = {
            "message": {
                "subject": subject,
                "body": {"contentType": body_type, "content": body},
                "toRecipients": to_list,
            },
        }
        if cc_recipients:
            payload["message"]["ccRecipients"] = [
                {"emailAddress": {"address": a.strip()}} for a in cc_recipients.split(";")
            ]
        if importance:
            payload["message"]["importance"] = importance
        return run_sync(graph().post("/me/sendMail", json=payload))
    return go()


@graph_tool("mail", "POST", "/me/messages", delegated=["Mail.ReadWrite"])
def create_draft(
    to_recipients: str,
    subject: str,
    body: str,
    body_type: str = "HTML",
    cc_recipients: str = None,
):
    """Create a mail draft for user review (does not send)."""
    def go():
        require_write()
        to_list = [{"emailAddress": {"address": a.strip()}} for a in to_recipients.split(";")]
        payload: dict = {
            "subject": subject,
            "body": {"contentType": body_type, "content": body},
            "toRecipients": to_list,
        }
        if cc_recipients:
            payload["ccRecipients"] = [
                {"emailAddress": {"address": a.strip()}} for a in cc_recipients.split(";")
            ]
        return run_sync(graph().post("/me/messages", json=payload))
    return go()


@graph_tool("mail", "POST", "/me/messages/{id}/send", delegated=["Mail.Send"])
def send_draft(message_id: str):
    def go():
        require_write()
        return run_sync(graph().post(f"/me/messages/{message_id}/send"))
    return go()


@graph_tool("mail", "POST", "/me/messages/{id}/reply", delegated=["Mail.Send"])
def reply_to_message(message_id: str, comment: str = None):
    def go():
        require_write()
        body = {"comment": comment} if comment else {}
        return run_sync(graph().post(f"/me/messages/{message_id}/reply", json=body))
    return go()


@graph_tool("mail", "POST", "/me/messages/{id}/replyAll", delegated=["Mail.Send"])
def reply_all_to_message(message_id: str, comment: str = None):
    def go():
        require_write()
        body = {"comment": comment} if comment else {}
        return run_sync(graph().post(f"/me/messages/{message_id}/replyAll", json=body))
    return go()


@graph_tool("mail", "POST", "/me/messages/{id}/forward", delegated=["Mail.Send"])
def forward_message(message_id: str, to_recipients: str, comment: str = None):
    def go():
        require_write()
        to_list = [{"emailAddress": {"address": a.strip()}} for a in to_recipients.split(";")]
        payload: dict = {"comment": comment or "", "toRecipients": to_list}
        return run_sync(graph().post(f"/me/messages/{message_id}/forward", json=payload))
    return go()


@graph_tool("mail", "PATCH", "/me/messages/{id}", delegated=["Mail.ReadWrite"])
def update_message(message_id: str, is_read: bool = None, flag_status: str = None):
    def go():
        require_write()
        body = {}
        if is_read is not None:
            body["isRead"] = is_read
        if flag_status is not None:
            body["flag"] = {"flagStatus": flag_status}
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/me/messages/{message_id}", json=body))
    return go()


@graph_tool("mail", "POST", "/me/messages/{id}/move", delegated=["Mail.ReadWrite"])
def move_message(message_id: str, destination_id: str):
    def go():
        require_write()
        return run_sync(graph().post(f"/me/messages/{message_id}/move", json={"destinationId": destination_id}))
    return go()


@graph_tool("mail", "DELETE", "/me/messages/{id}", delegated=["Mail.ReadWrite"])
def delete_message(message_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/messages/{message_id}"))
    return go()


@graph_tool("mail", "GET", "/me/mailboxSettings", delegated=["Mail.ReadWrite"])
def get_mailbox_settings():
    def go():
        return run_sync(graph().get("/me/mailboxSettings"))
    return go()


@graph_tool("mail", "PATCH", "/me/mailboxSettings", delegated=["Mail.ReadWrite"])
def update_mailbox_settings(automatic_replies_status: str = None, automatic_replies_body: str = None):
    """Update mailbox settings. automatic_replies_status: 'enabled', 'disabled', or 'scheduled'."""
    def go():
        require_write()
        body = {}
        if automatic_replies_status:
            body["automaticRepliesSetting"] = {"status": automatic_replies_status}
            if automatic_replies_body:
                body["automaticRepliesSetting"]["internalReplyMessage"] = automatic_replies_body
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch("/me/mailboxSettings", json=body))
    return go()


@graph_tool("mail", "GET", "/me/messages/delta", delegated=["Mail.Read"])
def delta_messages(delta_token: str = None, start_date_time: str = None):
    """Get message changes. For first call, omit delta_token. start_date_time: ISO 8601."""
    def go():
        if delta_token:
            return run_sync(graph().get(f"/me/messages/delta?$deltatoken={delta_token}"))
        params = to_query(**{"$filter": f"receivedDateTime ge {start_date_time}"}) if start_date_time else {}
        return run_sync(graph().get("/me/messages/delta", params=params))
    return go()
