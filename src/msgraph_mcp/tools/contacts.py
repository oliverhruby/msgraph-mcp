"""Contacts — personal contacts CRUD."""

from __future__ import annotations

from ._common import fail, graph, graph_tool, require_write, run_sync, to_query


@graph_tool("contacts", "GET", "/me/contacts", delegated=["Contacts.Read"])
def list_contacts(top: int = None, select: str = None, filter: str = None, order_by: str = None):
    def go():
        params = to_query(**{"$top": top, "$select": select, "$filter": filter, "$orderby": order_by})
        return run_sync(graph().get_all("/me/contacts", params=params))
    return go()


@graph_tool("contacts", "GET", "/me/contacts/{id}", delegated=["Contacts.Read"])
def get_contact(contact_id: str, select: str = None):
    def go():
        params = to_query(**{"$select": select})
        return run_sync(graph().get(f"/me/contacts/{contact_id}", params=params))
    return go()


@graph_tool("contacts", "GET", "/me/contactFolders", delegated=["Contacts.Read"])
def list_contact_folders():
    def go():
        return run_sync(graph().get_all("/me/contactFolders"))
    return go()


@graph_tool("contacts", "GET", "/me/contactFolders/{id}/contacts", delegated=["Contacts.Read"])
def list_folder_contacts(folder_id: str, top: int = None):
    def go():
        params = to_query(**{"$top": top})
        return run_sync(graph().get_all(f"/me/contactFolders/{folder_id}/contacts", params=params))
    return go()


@graph_tool("contacts", "POST", "/me/contacts", delegated=["Contacts.ReadWrite"])
def create_contact(
    given_name: str,
    surname: str,
    email_address: str = None,
    phone_number: str = None,
    company_name: str = None,
    job_title: str = None,
):
    def go():
        require_write()
        body: dict = {"givenName": given_name, "surname": surname}
        if email_address:
            body["emailAddresses"] = [{"address": email_address}]
        if phone_number:
            body["businessPhones"] = [phone_number]
        if company_name:
            body["companyName"] = company_name
        if job_title:
            body["jobTitle"] = job_title
        return run_sync(graph().post("/me/contacts", json=body))
    return go()


@graph_tool("contacts", "PATCH", "/me/contacts/{id}", delegated=["Contacts.ReadWrite"])
def update_contact(contact_id: str, given_name: str = None, surname: str = None, email_address: str = None, phone_number: str = None):
    def go():
        require_write()
        body = {}
        if given_name is not None:
            body["givenName"] = given_name
        if surname is not None:
            body["surname"] = surname
        if email_address is not None:
            body["emailAddresses"] = [{"address": email_address}]
        if phone_number is not None:
            body["businessPhones"] = [phone_number]
        if not body:
            return fail("No fields to update")
        return run_sync(graph().patch(f"/me/contacts/{contact_id}", json=body))
    return go()


@graph_tool("contacts", "DELETE", "/me/contacts/{id}", delegated=["Contacts.ReadWrite"])
def delete_contact(contact_id: str):
    def go():
        require_write()
        return run_sync(graph().delete(f"/me/contacts/{contact_id}"))
    return go()
