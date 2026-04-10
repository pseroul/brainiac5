# User Guide

Consensia is an idea management app that helps you capture, organise, and discover connections between your ideas using semantic similarity.

---

## Quick Start

1. Open Consensia in your browser
2. Enter your **email address** and the **6-digit code** from Google Authenticator
3. Click **Login**
4. Select or create a **Book** (a workspace for a topic or project)
5. Click **New Idea** to capture your first idea

That's it — your idea is saved and indexed for semantic search.

---

## Logging In

Consensia uses **TOTP authentication** (Time-based One-Time Passwords) instead of passwords. You need the Google Authenticator app (or any TOTP-compatible app such as Authy or 1Password) on your phone.

![Login screen](../screenshots/login.png)
*The login screen — enter your email and the current 6-digit OTP code.*

**Steps:**
1. Open Google Authenticator on your phone
2. Find the **Seroul Pierre / Consensia** entry
3. Type your email address and the current 6-digit code into the login form
4. Click **Login**

> **Note:** OTP codes refresh every 30 seconds. If login fails, wait for the next code and try again.

Your session lasts **30 minutes**. After that you will be automatically redirected to the login page.

---

## Managing Books

Books are workspaces — containers that group related ideas together. You might create one Book per project, topic, or area of interest.

![Books page](../screenshots/books.png)
*The Books page — create and manage your workspaces.*

### Create a book

1. Go to **My Books** in the navigation bar
2. Type a title in the input field
3. Click **Create**

### Select the active book

Use the **book selector** in the top navigation bar to switch between books. Most pages (Dashboard, Table of Contents, Tags) filter their content to the selected book.

### Add collaborators

Books can have multiple authors who can all view and edit ideas:

1. Go to **My Books**
2. Find your book and click **Manage Authors**
3. Select a user from the list and click **Add**

### Delete a book

Click the **Delete** button next to a book. This removes the book record only — ideas inside it are not automatically deleted.

---

## Working with Ideas

The **Dashboard** is the main workspace for capturing and managing ideas.

![Dashboard](../screenshots/dashboard.png)
*The Dashboard — your idea inbox.*

### Create an idea

1. Click **New Idea**
2. Fill in the **Title** (required) and **Content** (optional, supports free text)
3. Add **Tags** separated by commas (e.g. `machine learning, hardware, robotics`)
4. Click **Save**

The idea is immediately saved to the database and indexed for semantic search.

### Edit an idea

Click the **pencil icon** on any idea card to open the edit form. Modify the title, content, or tags and click **Save**.

### Delete an idea

Click the **trash icon** on an idea card. A confirmation dialog will appear. Confirm to permanently delete the idea.

> **Note:** Deletion also removes the idea from the semantic index. Tag relations are not automatically removed (a known limitation — see [architecture.md](architecture.md#key-design-decisions)).

### Search ideas

Type in the **search bar** at the top of the Dashboard to filter ideas by title in real time.

### Filter by book

Select a book in the top navigation bar. The Dashboard shows only ideas belonging to that book.

### Show only my ideas

Toggle **My Ideas** to display only ideas you created (useful in collaborative books).

---

## Semantic Features

Consensia does more than store ideas — it understands their meaning.

### Similar Ideas

On any idea card, click **Similar Ideas** to find the most semantically related ideas in your collection. This uses vector embeddings — ideas with similar language and concepts appear regardless of whether they share tags or keywords.

![Similar Ideas panel](../screenshots/similar-ideas.png)
*The Similar Ideas panel — discover unexpected connections.*

### Table of Contents

The **Table of Contents** page automatically organises your ideas into a two-level hierarchy (Sections → Chapters → Ideas) using machine learning clustering.

![Table of Contents](../screenshots/toc.png)
*The TOC — your ideas grouped into themes automatically.*

**To generate or refresh the TOC:**

1. Go to **Table of Contents**
2. Click **Update Structure**

> **Warning:** Updating the structure is computationally expensive (it re-runs the full ML clustering pipeline). On a Raspberry Pi 4 this takes 30–120 seconds depending on the number of ideas. Avoid clicking it repeatedly.

**Downloading the TOC:**

Click **Download** to export the Table of Contents as a Markdown file — useful for reports or presentations.

**Viewing idea content:**

Click any idea title in the TOC to open a modal with the full content.

---

## Tags & Ideas

The **Tags & Ideas** page gives you a tag-centric view of your collection.

![Tags & Ideas page](../screenshots/tags-ideas.png)
*Filter ideas by selecting a tag from the sidebar.*

- Click a **tag name** in the left panel to see all ideas with that tag
- Click **Delete tag** (trash icon) to remove an orphan tag that is no longer needed

> **Note:** Deleting a tag does not delete the ideas associated with it — only the tag label and its relations are removed.

---

## Voting

On the Dashboard, each idea card has **upvote** (▲) and **downvote** (▽) buttons. Use them to signal the quality or relevance of an idea.

- Click ▲ to upvote
- Click ▽ to downvote
- Click your current vote again to remove it

The **score** (upvotes minus downvotes) and **vote count** are displayed on each card.

---

## Admin Panel

> This section is only visible to users with the **admin** role.

The Admin Panel (`/admin`) lets you manage all user accounts.

![Admin panel](../screenshots/admin.png)
*The Admin Panel — manage users and their OTP credentials.*

### Create a new user

1. Go to **Admin** in the navigation bar
2. Fill in **Username**, **Email**, and toggle **Is Admin** if needed
3. Click **Create**
4. Copy the **OTP URI** displayed and send it to the new user — they will scan it with Google Authenticator to set up their account

### Edit a user

Click the **pencil icon** next to a user to update their username, email, or admin status.

### Delete a user

Click the **trash icon** next to a user. Guards prevent you from deleting yourself or the last admin account.

---

## Tips & Tricks

- **Tag consistently** — the TOC clustering works best when ideas share vocabulary. Use the same tag names for related concepts.
- **Content matters** — write a few sentences of content per idea. The embedding model weights content heavily; ideas with only a title cluster less accurately.
- **TOC is a snapshot** — it reflects the state of your ideas at the time you last clicked "Update Structure". Add a batch of ideas, then refresh once.
- **Keyboard shortcut** — press `Escape` to close any open modal.
