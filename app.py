import os
from functools import wraps
from datetime import date
from sqlalchemy import func
import calendar



from flask import (
    Flask, render_template, request, redirect,
    url_for, session, jsonify, abort, flash
)
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()

app = Flask(
    __name__,
    static_folder="statics",
    template_folder="templates"
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "super-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://neondb_owner:npg_1WXhKSw5RslY@ep-little-forest-a4u639bf-pooler.us-east-1.aws.neon.tech/artist_db?sslmode=require&channel_binding=require"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------------- MODELS ---------------------- #

class Project(db.Model):
    __tablename__ = "projects"

    project_id = db.Column(db.String(10), primary_key=True)
    release_date = db.Column(db.Date)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))
    title = db.Column(db.String(200))
    song_link = db.Column(db.Text)
    album_art = db.Column(db.Text)

    views = db.relationship("View", backref="project", lazy="dynamic")


class Artist(db.Model):
    __tablename__ = "artists"

    artist_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo_url = db.Column(db.Text)
    last_project_id = db.Column(
        db.String(10),
        db.ForeignKey("projects.project_id"),
        nullable=True
    )

    last_project = db.relationship("Project", foreign_keys=[last_project_id])
    rankings = db.relationship("Ranking", backref="artist", lazy="dynamic")
    events = db.relationship("ArtistCalendar", backref="artist", lazy="dynamic")


class Production(db.Model):
    __tablename__ = "productions"

    production_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    logo_url = db.Column(db.Text)
    market_value = db.Column(db.BigInteger)
    last_project_id = db.Column(
        db.String(10),
        db.ForeignKey("projects.project_id"),
        nullable=True
    )

    last_project = db.relationship("Project", foreign_keys=[last_project_id])


class Distributor(db.Model):
    __tablename__ = "distributors"

    distributor_id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    logo_url = db.Column(db.Text)
    url = db.Column(db.Text)
    market_value = db.Column(db.BigInteger)


class Collaboration(db.Model):
    __tablename__ = "collaborations"

    colab_id = db.Column(db.String(10), primary_key=True)
    artist_id = db.Column(
        db.String(10),
        db.ForeignKey("artists.artist_id"),
        nullable=False
    )
    production_id = db.Column(
        db.String(10),
        db.ForeignKey("productions.production_id"),
        nullable=False
    )
    distributor_id = db.Column(
        db.String(10),
        db.ForeignKey("distributors.distributor_id"),
        nullable=False
    )
    project_id = db.Column(
        db.String(10),
        db.ForeignKey("projects.project_id"),
        nullable=False
    )


class ArtistCalendar(db.Model):
    __tablename__ = "artist_calendar"

    event_id = db.Column(db.String(10), primary_key=True)
    artist_id = db.Column(
        db.String(10),
        db.ForeignKey("artists.artist_id"),
        nullable=False
    )
    event_date = db.Column(db.Date)
    description = db.Column(db.Text)


class View(db.Model):
    __tablename__ = "views"

    stat_id = db.Column(db.String(10), primary_key=True)
    project_id = db.Column(
        db.String(10),
        db.ForeignKey("projects.project_id"),
        nullable=False
    )
    views_count = db.Column(db.BigInteger)
    recorded_date = db.Column(db.Date)


class Ranking(db.Model):
    __tablename__ = "rankings"

    ranking_id = db.Column(db.String(10), primary_key=True)
    artist_id = db.Column(
        db.String(10),
        db.ForeignKey("artists.artist_id"),
        nullable=False
    )
    ranking_position = db.Column(db.Integer)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    # Map to existing DB column "password"
    password_hash = db.Column("password", db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)


# ---------------------- HELPERS ---------------------- #

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "role" not in session:
                return redirect(url_for("login"))
            if session["role"] not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


# ---------------------- ROUTES ---------------------- #

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(username=username).first()
        if user and user.password_hash == password:
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    # Key metrics
    total_projects = Project.query.count()
    total_artists = Artist.query.count()
    total_productions = Production.query.count()
    total_distributors = Distributor.query.count()

    # Artists + rankings + events
    artists = Artist.query.all()
    rankings = {r.artist_id: r.ranking_position for r in Ranking.query.all()}
    calendars = {}
    for e in ArtistCalendar.query.all():
        calendars.setdefault(e.artist_id, []).append(e)

    # Productions & distributors
    productions = Production.query.all()
    distributors = Distributor.query.all()

    # Latest project views
    views = {}
    for v in View.query.all():
        if v.project_id not in views or v.recorded_date > views[v.project_id]["recorded_date"]:
            views[v.project_id] = {
                "views": v.views_count,
                "recorded_date": v.recorded_date
            }

    return render_template(
        "dashboard.html",
        user_role=session.get("role"),
        username=session.get("username"),
        total_projects=total_projects,
        total_artists=total_artists,
        total_productions=total_productions,
        total_distributors=total_distributors,
        artists=artists,
        rankings=rankings,
        calendars=calendars,
        productions=productions,
        distributors=distributors,
        views=views,
        today=date.today()
    )


# ----------- SIMPLE INSERT / DELETE API (Admin / Manager) ----------- #

@app.route("/api/insert", methods=["POST"])
@login_required
@role_required("admin", "manager")
def api_insert():
    entity = request.json.get("entity")
    data = request.json.get("data", {})

    try:
        if entity == "artist":
            a = Artist(
                artist_id=data["artist_id"],
                name=data["name"],
                photo_url=data.get("photo_url"),
                last_project_id=data.get("last_project_id")
            )
            db.session.add(a)

        elif entity == "project":
            p = Project(
                project_id=data["project_id"],
                title=data.get("title"),
                type=data.get("type"),
                description=data.get("description"),
                song_link=data.get("song_link"),
                album_art=data.get("album_art"),
                release_date=data.get("release_date")
            )
            db.session.add(p)

        elif entity == "production":
            pr = Production(
                production_id=data["production_id"],
                name=data["name"],
                logo_url=data.get("logo_url"),
                market_value=data.get("market_value"),
                last_project_id=data.get("last_project_id")
            )
            db.session.add(pr)

        elif entity == "distributor":
            d = Distributor(
                distributor_id=data["distributor_id"],
                name=data["name"],
                logo_url=data.get("logo_url"),
                url=data.get("url"),
                market_value=data.get("market_value")
            )
            db.session.add(d)

        else:
            return jsonify({"ok": False, "message": "Unknown entity"}), 400

        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/delete", methods=["POST"])
@login_required
@role_required("admin")
def api_delete():
    entity = request.json.get("entity")
    object_id = request.json.get("id")

    model_map = {
        "artist": Artist,
        "project": Project,
        "production": Production,
        "distributor": Distributor,
    }
    model = model_map.get(entity)
    if not model:
        return jsonify({"ok": False, "message": "Unknown entity"}), 400

    obj = model.query.get(object_id)
    if not obj:
        return jsonify({"ok": False, "message": "Not found"}), 404

    try:
        db.session.delete(obj)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500


# ---------------------- SEARCH ---------------------- #

@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})

    like = f"%{q}%"
    results = []

    for a in Artist.query.filter(Artist.name.ilike(like)).limit(5):
        results.append({
            "type": "artist",
            "id": a.artist_id,
            "label": a.name
        })

    for p in Project.query.filter(Project.title.ilike(like)).limit(5):
        results.append({
            "type": "project",
            "id": p.project_id,
            "label": p.title,
            "song_link": p.song_link
        })

    for pr in Production.query.filter(Production.name.ilike(like)).limit(5):
        results.append({
            "type": "production",
            "id": pr.production_id,
            "label": pr.name
        })

    for d in Distributor.query.filter(Distributor.name.ilike(like)).limit(5):
        results.append({
            "type": "distributor",
            "id": d.distributor_id,
            "label": d.name
        })

    return jsonify({"results": results})

# ---------------------- DETAIL DASHBOARDS ---------------------- #

def build_month_calendar(events):
    """Return (year, month_name, weeks, busy_days_set) for a simple month view."""
    # Keep only events that actually have a date
    dated_events = [e for e in events if e.event_date is not None]

    if dated_events:
        ref = min(e.event_date for e in dated_events)
    else:
        ref = date.today()

    year = ref.year
    month = ref.month
    month_name = calendar.month_name[month]

    cal = calendar.Calendar(firstweekday=0)

    # Busy days = set of day numbers in this month
    busy_days = {
        e.event_date.day
        for e in dated_events
        if e.event_date.year == year and e.event_date.month == month
    }

    weeks = []
    week = []
    for d in cal.itermonthdates(year, month):
        if len(week) == 7:
            weeks.append(week)
            week = []
        # show 0 for overflow days from previous/next month
        week.append(d.day if d.month == month else 0)
    if week:
        while len(week) < 7:
            week.append(0)
        weeks.append(week)

    return year, month_name, weeks, busy_days


@app.route("/artist/<artist_id>")
@login_required
def artist_detail(artist_id):
    artist = Artist.query.get_or_404(artist_id)
    ranking = Ranking.query.filter_by(artist_id=artist_id).first()
    events = (
        ArtistCalendar.query.filter_by(artist_id=artist_id)
        .order_by(ArtistCalendar.event_date)
        .all()
    )

    collabs = (
        db.session.query(Collaboration, Project, Production, Distributor)
        .join(Project, Collaboration.project_id == Project.project_id)
        .join(Production, Collaboration.production_id == Production.production_id)
        .join(Distributor, Collaboration.distributor_id == Distributor.distributor_id)
        .filter(Collaboration.artist_id == artist_id)
        .all()
    )

    # Distinct sets for counts
    project_ids = {p.project_id for _, p, _, _ in collabs}
    production_ids = {pr.production_id for _, _, pr, _ in collabs}
    distributor_ids = {d.distributor_id for _, _, _, d in collabs}

    # Total views
    total_views = (
        db.session.query(func.coalesce(func.sum(View.views_count), 0))
        .join(Project, View.project_id == Project.project_id)
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .filter(Collaboration.artist_id == artist_id)
        .scalar()
    )

    # Top projects by views
    top_projects = (
        db.session.query(
            Project.project_id,
            Project.title,
            Project.song_link,
            func.coalesce(func.sum(View.views_count), 0).label("views"),
        )
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .outerjoin(View, View.project_id == Project.project_id)
        .filter(Collaboration.artist_id == artist_id)
        .group_by(Project.project_id)
        .order_by(func.coalesce(func.sum(View.views_count), 0).desc())
        .limit(5)
        .all()
    )

    # Last release from collabs (by release_date)
    last_release = None
    if collabs:
        projects_unique = {p.project_id: p for _, p, _, _ in collabs}.values()
        last_release = max(
            projects_unique,
            key=lambda p: p.release_date or date.min,
        )

    cal_year, cal_month_name, cal_weeks, cal_busy_days = build_month_calendar(events)

    return render_template(
        "artist_detail.html",
        artist=artist,
        ranking=ranking,
        events=events,
        collabs=collabs,
        total_views=total_views,
        num_projects=len(project_ids),
        num_productions=len(production_ids),
        num_distributors=len(distributor_ids),
        top_projects=top_projects,
        last_release=last_release,
        cal_year=cal_year,
        cal_month_name=cal_month_name,
        cal_weeks=cal_weeks,
        cal_busy_days=cal_busy_days,
        username=session.get("username"),
        user_role=session.get("role"),
    )


@app.route("/production/<production_id>")
@login_required
def production_detail(production_id):
    production = Production.query.get_or_404(production_id)

    collabs = (
        db.session.query(Collaboration, Project, Artist, Distributor)
        .join(Project, Collaboration.project_id == Project.project_id)
        .join(Artist, Collaboration.artist_id == Artist.artist_id)
        .join(Distributor, Collaboration.distributor_id == Distributor.distributor_id)
        .filter(Collaboration.production_id == production_id)
        .all()
    )

    project_ids = {p.project_id for _, p, _, _ in collabs}
    artist_ids = {a.artist_id for _, _, a, _ in collabs}
    distributor_ids = {d.distributor_id for _, _, _, d in collabs}

    total_views = (
        db.session.query(func.coalesce(func.sum(View.views_count), 0))
        .join(Project, View.project_id == Project.project_id)
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .filter(Collaboration.production_id == production_id)
        .scalar()
    )

    top_projects = (
        db.session.query(
            Project.project_id,
            Project.title,
            Project.song_link,
            func.coalesce(func.sum(View.views_count), 0).label("views"),
        )
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .outerjoin(View, View.project_id == Project.project_id)
        .filter(Collaboration.production_id == production_id)
        .group_by(Project.project_id)
        .order_by(func.coalesce(func.sum(View.views_count), 0).desc())
        .limit(5)
        .all()
    )

    # Last release for this production
    last_release = None
    if collabs:
        projects_unique = {p.project_id: p for _, p, _, _ in collabs}.values()
        last_release = max(
            projects_unique,
            key=lambda p: p.release_date or date.min,
        )

    return render_template(
        "production_detail.html",
        production=production,
        collabs=collabs,
        total_views=total_views,
        num_projects=len(project_ids),
        num_artists=len(artist_ids),
        num_distributors=len(distributor_ids),
        top_projects=top_projects,
        last_release=last_release,
        username=session.get("username"),
        user_role=session.get("role"),
    )

@app.route("/distributor/<distributor_id>")
@login_required
def distributor_detail(distributor_id):
    distributor = Distributor.query.get_or_404(distributor_id)

    collabs = (
        db.session.query(Collaboration, Project, Artist, Production)
        .join(Project, Collaboration.project_id == Project.project_id)
        .join(Artist, Collaboration.artist_id == Artist.artist_id)
        .join(Production, Collaboration.production_id == Production.production_id)
        .filter(Collaboration.distributor_id == distributor_id)
        .all()
    )

    project_ids = {p.project_id for _, p, _, _ in collabs}
    artist_ids = {a.artist_id for _, _, a, _ in collabs}
    production_ids = {pr.production_id for _, _, _, pr in collabs}

    total_views = (
        db.session.query(func.coalesce(func.sum(View.views_count), 0))
        .join(Project, View.project_id == Project.project_id)
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .filter(Collaboration.distributor_id == distributor_id)
        .scalar()
    )

    top_projects = (
        db.session.query(
            Project.project_id,
            Project.title,
            Project.song_link,
            func.coalesce(func.sum(View.views_count), 0).label("views"),
        )
        .join(Collaboration, Collaboration.project_id == Project.project_id)
        .outerjoin(View, View.project_id == Project.project_id)
        .filter(Collaboration.distributor_id == distributor_id)
        .group_by(Project.project_id)
        .order_by(func.coalesce(func.sum(View.views_count), 0).desc())
        .limit(5)
        .all()
    )

    # Last release by this distributor
    last_release = None
    if collabs:
        projects_unique = {p.project_id: p for _, p, _, _ in collabs}.values()
        last_release = max(
            projects_unique,
            key=lambda p: p.release_date or date.min,
        )

    return render_template(
        "distributor_detail.html",
        distributor=distributor,
        collabs=collabs,
        total_views=total_views,
        num_projects=len(project_ids),
        num_artists=len(artist_ids),
        num_productions=len(production_ids),
        top_projects=top_projects,
        last_release=last_release,
        username=session.get("username"),
        user_role=session.get("role"),
    )

# ---------------------- ERRORS ---------------------- #

@app.errorhandler(403)
def forbidden(e):
    return render_template("403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
