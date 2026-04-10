# API Reference

All endpoints are served at the base path configured in nginx (`/api/` in production, `http://localhost:8000` in development).

## Authentication

All endpoints except `POST /verify-otp` and `GET /health` require a valid JWT in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Admin-only endpoints additionally require `is_admin = true` on the authenticated user.

---

## Authentication

### `POST /verify-otp`

Authenticate with email and TOTP code. Returns a JWT on success.

**Auth required:** No

**Request body:**

```json
{
  "email": "user@example.com",
  "otp_code": "123456"
}
```

**Response `200`:**

```json
{
  "status": "success",
  "message": "OTP verified successfully",
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

**Response `401`:**

```json
{ "detail": "Invalid or expired OTP" }
```

---

## Ideas

### `GET /ideas`

List all ideas, optionally filtered by book.

**Auth required:** Bearer

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `book_id` | integer | No | Filter to a specific book |

**Response `200`:**

```json
[
  {
    "id": 1,
    "title": "My idea",
    "content": "Idea content",
    "tags": "tag1;tag2",
    "book_id": 1
  }
]
```

---

### `GET /user/ideas`

List ideas owned by the currently authenticated user.

**Auth required:** Bearer

**Response `200`:** Same schema as `GET /ideas`.

---

### `GET /ideas/tags/{tags}`

Filter ideas by one or more tags.

**Auth required:** Bearer

**Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `tags` | string | Semicolon-separated tag names, e.g. `ai;hardware` |

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `book_id` | integer | No | Further filter to a specific book |

**Response `200`:** Same schema as `GET /ideas`.

---

### `GET /ideas/search/{subname}`

Search ideas by partial title match.

**Auth required:** Bearer

**Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `subname` | string | Substring to search in idea titles |

**Response `200`:** Same schema as `GET /ideas`.

---

### `GET /ideas/{idea_id}/content`

Get the plain-text content of a single idea.

**Auth required:** Bearer

**Response `200`:** `"The full content text as a string"`

---

### `GET /ideas/similar/{idea}`

Get ideas semantically similar to a given idea title, using vector similarity search.

**Auth required:** Bearer

**Path parameters:**

| Parameter | Type | Description |
|---|---|---|
| `idea` | string | Title of the reference idea |

**Response `200`:** Same schema as `GET /ideas`. Up to 10 results.

---

### `POST /ideas`

Create a new idea.

**Auth required:** Bearer

**Request body:**

```json
{
  "title": "My idea",
  "content": "Detailed content",
  "tags": "tag1;tag2",
  "book_id": 1
}
```

- `tags`: semicolon-separated tag names. Tags that do not exist are created automatically.
- `book_id`: required — every idea must belong to a book.

**Response `200`:**

```json
{ "id": 42 }
```

> **Note:** If `owner_email` does not match any user, the response returns `{"id": -1}` instead of a 4xx error (known quirk).

---

### `PUT /ideas/{id}`

Update an existing idea.

**Auth required:** Bearer

**Path parameters:** `id` — idea ID

**Request body:**

```json
{
  "title": "Updated title",
  "content": "Updated content",
  "tags": "newtag;anothertag"
}
```

Tag relations are reconciled: new tags are added, removed tags are unlinked.

**Response `200`:**

```json
{ "message": "Idea updated successfully" }
```

---

### `DELETE /ideas/{id}`

Delete an idea.

**Auth required:** Bearer

> **Note:** `DELETE` requests with a body must use `client.request()` in tests — `httpx.Client.delete()` does not support `json=` bodies.

**Request body:**

```json
{
  "title": "Idea to delete",
  "content": "Its content"
}
```

**Response `200`:**

```json
{ "message": "Idea deleted successfully" }
```

---

## Tags

### `GET /tags`

List all tags.

**Auth required:** Bearer

**Query parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `book_id` | integer | No | Only return tags used in a specific book |

**Response `200`:**

```json
[{ "name": "machine learning" }, { "name": "hardware" }]
```

---

### `GET /ideas/{idea_id}/tags`

List tags attached to a specific idea.

**Auth required:** Bearer

**Response `200`:**

```json
["machine learning", "hardware"]
```

---

### `POST /tags`

Create a new tag.

**Auth required:** Bearer

**Request body:**

```json
{ "name": "new-tag" }
```

**Response `200`:**

```json
{ "message": "Tag added successfully" }
```

---

### `DELETE /tags/{name}`

Delete a tag by name.

**Auth required:** Bearer

**Path parameters:** `name` — tag name

**Response `200`:**

```json
{ "message": "Tag deleted successfully" }
```

> **Note:** Deleting a tag does not cascade to `relations` rows (no FK enforcement). Orphan relations may remain.

---

## Relations

Relations link ideas to tags (many-to-many).

### `POST /relations`

Link an idea to a tag.

**Auth required:** Bearer

**Request body:**

```json
{ "idea_id": 1, "tag_name": "hardware" }
```

**Response `200`:**

```json
{ "message": "Relation added successfully" }
```

---

### `DELETE /relations`

Unlink an idea from a tag.

**Auth required:** Bearer

> **Note:** Use `client.request("DELETE", "/relations", json=...)` in tests.

**Request body:**

```json
{ "idea_id": 1, "tag_name": "hardware" }
```

**Response `200`:**

```json
{ "message": "Relation removed successfully" }
```

---

## Books

### `GET /books`

List all books.

**Auth required:** Bearer

**Response `200`:**

```json
[{ "id": 1, "title": "My Project" }]
```

---

### `POST /books`

Create a new book.

**Auth required:** Bearer

**Request body:**

```json
{ "title": "My New Book" }
```

**Response `200`:**

```json
{ "id": 2 }
```

---

### `DELETE /books/{book_id}`

Delete a book.

**Auth required:** Bearer

**Path parameters:** `book_id` — book ID

**Response `200`:**

```json
{ "message": "Book deleted successfully" }
```

---

### `GET /books/{book_id}/authors`

List users who are authors of a book.

**Auth required:** Bearer

**Response `200`:**

```json
[{ "id": 1, "username": "alice", "email": "alice@example.com" }]
```

---

## Book Authors

### `POST /book-authors`

Add a user as an author of a book.

**Auth required:** Bearer

**Request body:**

```json
{ "book_id": 1, "user_id": 2 }
```

**Response `200`:**

```json
{ "message": "Book author added successfully" }
```

---

### `DELETE /book-authors`

Remove a user from a book's author list.

**Auth required:** Bearer

**Request body:**

```json
{ "book_id": 1, "user_id": 2 }
```

**Response `200`:**

```json
{ "message": "Book author removed successfully" }
```

---

## Voting

### `GET /ideas/{idea_id}/votes`

Get the vote summary for an idea and the current user's vote.

**Auth required:** Bearer

**Response `200`:**

```json
{
  "score": 3,
  "count": 5,
  "user_vote": 1
}
```

- `score`: sum of all vote values (upvotes − downvotes)
- `count`: total number of votes cast
- `user_vote`: `1`, `-1`, or `null` (no vote)

---

### `POST /ideas/{idea_id}/vote`

Cast or change a vote on an idea.

**Auth required:** Bearer

**Request body:**

```json
{ "value": 1 }
```

- `value`: `1` (upvote) or `-1` (downvote)

**Response `200`:** Same schema as `GET /ideas/{idea_id}/votes`.

**Response `400`:** If `value` is not `1` or `-1`.

**Response `404`:** If the user or idea does not exist.

---

### `DELETE /ideas/{idea_id}/vote`

Remove the current user's vote from an idea.

**Auth required:** Bearer

**Response `200`:** Same schema as `GET /ideas/{idea_id}/votes`.

---

## Table of Contents

### `GET /toc/structure`

Get the cached hierarchical TOC structure. If no cache exists, generates it on demand (expensive).

**Auth required:** Bearer

**Response `200`:** A nested JSON array representing sections → chapters → ideas.

```json
[
  {
    "title": "Machine Learning & Hardware",
    "type": "heading",
    "level": 1,
    "children": [
      {
        "title": "Edge Computing",
        "type": "heading",
        "level": 2,
        "children": [
          {
            "id": 1,
            "title": "Raspberry Pi cluster",
            "type": "idea",
            "text": "Idea content...",
            "originality": 0.82
          }
        ]
      }
    ]
  }
]
```

---

### `POST /toc/update`

Regenerate the TOC structure from scratch. Triggers the full ML clustering pipeline.

**Auth required:** Bearer

> **Warning:** This is computationally expensive. On a Raspberry Pi 4 it can take 30–120 seconds.

**Response `200`:**

```json
{ "message": "TOC structure updated successfully" }
```

---

## Users

### `GET /users`

List all users (basic info — for book author assignment).

**Auth required:** Bearer

**Response `200`:**

```json
[{ "id": 1, "username": "alice", "email": "alice@example.com" }]
```

---

## Admin — User Management

> All `/admin/*` endpoints require the `is_admin` flag on the authenticated user.

### `GET /admin/users`

List all users with admin status.

**Auth required:** Bearer + Admin

**Response `200`:**

```json
[{ "id": 1, "username": "alice", "email": "alice@example.com", "is_admin": true }]
```

---

### `POST /admin/users`

Create a new user. Generates a TOTP secret and returns the provisioning URI for Google Authenticator setup.

**Auth required:** Bearer + Admin

**Request body:**

```json
{
  "username": "bob",
  "email": "bob@example.com",
  "is_admin": false
}
```

**Response `200`:**

```json
{
  "id": 2,
  "username": "bob",
  "email": "bob@example.com",
  "is_admin": false,
  "otp_uri": "otpauth://totp/..."
}
```

**Response `409`:** Username or email already exists.

---

### `PUT /admin/users/{user_id}`

Update a user's profile.

**Auth required:** Bearer + Admin

**Request body:**

```json
{
  "username": "bobby",
  "email": "bobby@example.com",
  "is_admin": true
}
```

**Response `200`:**

```json
{ "id": 2, "username": "bobby", "email": "bobby@example.com", "is_admin": true }
```

**Response `404`:** User not found.

**Response `409`:** Username or email conflict.

---

### `DELETE /admin/users/{user_id}`

Delete a user account.

**Auth required:** Bearer + Admin

**Guards:**
- Cannot delete yourself
- Cannot delete the last admin account

**Response `200`:**

```json
{ "message": "User deleted successfully" }
```

**Response `400`:** Guard violation (self-delete or last admin).

**Response `404`:** User not found.

---

## Health

### `GET /health`

Health check — no auth required.

**Response `200`:**

```json
{ "status": "healthy" }
```
