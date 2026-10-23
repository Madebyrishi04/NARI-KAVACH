
import { useCallback, useEffect, useState } from "react";
import "./Contacts.css";

const API_URL = "http://127.0.0.1:8000/emergency-contacts/";

function Contacts({ token }) {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const emptyForm = {
    contact_name: "",
    phone_number: "",
    email: "",
    relationship: "",
  };

  const [form, setForm] = useState(emptyForm);

  const loadContacts = useCallback(async () => {
    if (!token) {
      setError("Please log in to view trusted contacts.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Could not load trusted contacts."
        );
      }

      setContacts(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Could not load trusted contacts.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadContacts();
  }, [loadContacts]);

  const openAddForm = () => {
    setForm(emptyForm);
    setEditingId(null);
    setShowForm(true);
    setError("");
    setMessage("");
  };

  const openEditForm = (contact) => {
    setForm({
      contact_name: contact.contact_name || "",
      phone_number: contact.phone_number || "",
      email: contact.email || "",
      relationship: contact.relationship || "",
    });

    setEditingId(contact.id);
    setShowForm(true);
    setError("");
    setMessage("");
  };

  const saveContact = async (event) => {
    event.preventDefault();

    if (!token || saving) return;

    setSaving(true);
    setError("");
    setMessage("");

    try {
      const url = editingId
        ? `${API_URL}${editingId}`
        : API_URL;

      const response = await fetch(url, {
        method: editingId ? "PUT" : "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          contact_name: form.contact_name.trim(),
          phone_number: form.phone_number.trim(),
          email: form.email.trim() || null,
          relationship: form.relationship.trim() || null,
        }),
      });

      const data =
        response.status === 204 ? null : await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Could not save this contact."
        );
      }

      setShowForm(false);
      setForm(emptyForm);
      setEditingId(null);

      setMessage(
        editingId
          ? "Trusted contact updated successfully."
          : "Trusted contact added successfully."
      );

      await loadContacts();
    } catch (err) {
      setError(err.message || "Could not save this contact.");
    } finally {
      setSaving(false);
    }
  };

  const deleteContact = async (contact) => {
    if (deletingId !== null) return;

    if (
      !window.confirm(
        `Delete ${contact.contact_name} from trusted contacts?`
      )
    ) {
      return;
    }

    setDeletingId(contact.id);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_URL}${contact.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(
          data.detail || "Could not delete this contact."
        );
      }

      setContacts((previous) =>
        previous.filter((item) => item.id !== contact.id)
      );

      setMessage("Trusted contact deleted successfully.");
    } catch (err) {
      setError(err.message || "Could not delete this contact.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="contacts-page">
      <header className="contacts-heading">
        <div>
          <h1>Trusted contacts</h1>
          <p>
            Manage the people you trust in an emergency.
            Contact notifications are not sent by this screen.
          </p>
        </div>

        <button
          className="contacts-refresh"
          type="button"
          onClick={loadContacts}
          disabled={loading}
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </header>

      {message && (
        <p className="contacts-message success">{message}</p>
      )}

      {error && (
        <p className="contacts-message error">{error}</p>
      )}

      {loading ? (
        <div className="contacts-empty">Loading contacts...</div>
      ) : (
        <div className="contacts-list">
          {contacts.map((contact) => {
            const initials = contact.contact_name
              .trim()
              .split(/\s+/)
              .slice(0, 2)
              .map((part) => part[0])
              .join("")
              .toUpperCase();

            return (
              <article className="contact-card" key={contact.id}>
                <div className="contact-avatar">{initials}</div>

                <div className="contact-details">
                  <h3>{contact.contact_name}</h3>
                  <p>
                    {contact.relationship || "Trusted contact"}
                    {" · "}
                    {contact.phone_number}
                  </p>

                  {contact.email && (
                    <p>{contact.email}</p>
                  )}
                </div>

                <div className="contact-actions">
                  <button
                    type="button"
                    onClick={() => openEditForm(contact)}
                    disabled={deletingId !== null || saving}
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    className="delete-contact"
                    onClick={() => deleteContact(contact)}
                    disabled={deletingId !== null || saving}
                  >
                    {deletingId === contact.id
                      ? "Deleting..."
                      : "Delete"}
                  </button>
                </div>
              </article>
            );
          })}

          {!contacts.length && (
            <div className="contacts-empty">
              <h3>No trusted contacts yet</h3>
              <p>
                Add someone you trust to your emergency contact list.
              </p>
            </div>
          )}
        </div>
      )}

      <button
        type="button"
        className="add-contact-button"
        onClick={openAddForm}
      >
        + Add trusted contact
      </button>

      {showForm && (
        <div className="contact-form-backdrop">
          <form className="contact-form" onSubmit={saveContact}>
            <div className="contact-form-heading">
              <h2>{editingId ? "Edit contact" : "New contact"}</h2>

              <button
                type="button"
                onClick={() => setShowForm(false)}
                disabled={saving}
                aria-label="Close form"
              >
                ×
              </button>
            </div>

            <label htmlFor="contact-name">Name</label>
            <input
              id="contact-name"
              value={form.contact_name}
              onChange={(event) =>
                setForm({
                  ...form,
                  contact_name: event.target.value,
                })
              }
              minLength={2}
              maxLength={100}
              required
            />

            <label htmlFor="contact-phone">Phone</label>
            <input
              id="contact-phone"
              type="tel"
              value={form.phone_number}
              onChange={(event) =>
                setForm({
                  ...form,
                  phone_number: event.target.value,
                })
              }
              minLength={10}
              maxLength={20}
              placeholder="+91..."
              required
            />

            <label htmlFor="contact-email">Email address</label>
            <input
              id="contact-email"
              type="email"
              value={form.email}
              onChange={(event) =>
                setForm({
                  ...form,
                  email: event.target.value,
                })
              }
              maxLength={255}
              placeholder="contact@example.com"
            />

            <label htmlFor="contact-relationship">Relationship</label>
            <input
              id="contact-relationship"
              value={form.relationship}
              onChange={(event) =>
                setForm({
                  ...form,
                  relationship: event.target.value,
                })
              }
              maxLength={50}
              placeholder="e.g. Sister, Friend"
            />

            <button
              type="submit"
              className="save-contact-button"
              disabled={saving}
            >
              {saving
                ? "Saving..."
                : editingId
                  ? "Update contact"
                  : "Save contact"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default Contacts;
