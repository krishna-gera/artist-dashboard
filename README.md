# 🎨 Artist Dashboard

**Artist Dashboard** is a full-stack web application built using **Flask + PostgreSQL** for managing artists, projects, collaborations, rankings, and analytics in a structured, role-based system.

This project demonstrates backend architecture, relational database design, authentication, and dashboard analytics.

---

## 🚀 Features

* 🔐 **Role-based authentication system**
* 📊 **Interactive dashboard** with key metrics
* 🎵 **Artist & project management**
* 🤝 **Collaboration tracking**
* 📈 **Rankings and view analytics**
* 🔎 **Search functionality**
* 🗄 **PostgreSQL** relational database integration

---

## 🛠 Tech Stack

| Component | Technology |
| --- | --- |
| **Backend** | Python, Flask |
| **Database** | PostgreSQL (Hosted on Neon - AWS us-east-1) |
| **ORM** | SQLAlchemy |
| **Frontend** | HTML, CSS, Jinja Templates |
| **Server** | Gunicorn (Production-ready deployment) |

---

## 🗄 Database

The application uses **PostgreSQL** as the primary database. Connection is configured via the environment variable `DATABASE_URL`.

The schema (available in `schema.sql`) includes the following tables:

* `users`, `artists`, `projects`, `productions`
* `distributors`, `collaborations`, `views`, `rankings`
* `artist_calendar`

---

## 🔐 Demo Login Credentials

> [!IMPORTANT]
> These credentials are for demonstration purposes only.

| Role | Username | Password |
| --- | --- | --- |
| **User** | `user` | `u1` |

*This account has standard user-level access for viewing dashboard data.*

---

## 📦 Local Setup Instructions

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/krishna-gera/artist-dashboard.git
cd artist-dashboard

```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate   
# Windows
venv\Scripts\activate      

```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt

```

### 4️⃣ Configure Environment Variables

Create a `.env` file or set the following in your environment:

```env
DATABASE_URL=your_postgresql_connection_string
SECRET_KEY=your_secret_key

```

### 5️⃣ Run the Application

```bash
python app.py

```

---

## 🌍 Deployment

This project is optimized for deployment on:

* **Render** (Web Service)
* **Neon PostgreSQL** (Database)

*Ensure `DATABASE_URL` is properly configured in your hosting environment's variables.*

---

## 👨‍💻 Author

**Krishna Gera**
