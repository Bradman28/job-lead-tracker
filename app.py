import sqlite3
# flask creates application, RT loads HTML template passes python data into it, request reads info sent by browser, redirect sends browser to route after an update, url_for builds route URL using name of flask function
from flask import Flask, render_template, request, redirect, url_for

# create flask application, name tells flask which python file is currently running
app = Flask(__name__)

# tells flask to run this function when browser is on root URL
@app.route("/")
def index():
    conn = sqlite3.connect("jobs.db")

    # row factory to access values by column name
    conn.row_factory = sqlite3.Row

    # looks for values in URL, second argument prevents filter from being None when nothing is selected
    request_alert_name = request.args.get("alert_name", "")
    interested = request.args.get("interested", "")
    applied = request.args.get("applied", "")
    selected_company = request.args.get("company", "")
    selected_location = request.args.get("location", "")

    # pagination variables, look for page in URL, max 50 rows per page, calculate how many rows to skip for each page ie 50
    page = request.args.get("page", 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page

    where_clause = " WHERE is_archived = 0"
    params = []

    # runs through code and adds AND to SQL block for each selection (or non selection)
    if request_alert_name:
        where_clause += " AND alert_name = ?"
        params.append(request_alert_name)
    
    if interested:
        if interested == "Blank":
            where_clause += " AND (interested IS NULL OR interested = '')"
        else:
            where_clause += " AND interested = ?"
            params.append(interested)
    
    if applied:
        if applied == "Blank":
            where_clause += " AND (applied IS NULL OR applied = '')"
        else:
            where_clause += " AND applied = ?"
            params.append(applied)
    
    if selected_company:
        where_clause += " AND company = ?"
        params.append(selected_company)
    
    if selected_location:
        where_clause += " AND location = ?"
        params.append(selected_location)

    count_query = "SELECT COUNT(*) FROM jobs" + where_clause

    total_jobs = conn.execute(count_query, params).fetchone()[0]
    total_pages = max(1, (total_jobs + per_page - 1) // per_page)

    # start with active jobs only, additional filters pended below
    query = """
        SELECT
            id,
            job_title,
            company,
            location,
            job_link,
            alert_name,
            interested,
            applied,
            interview,
            date_added, 
            posting_status
        FROM jobs
    """ + where_clause + """
        ORDER BY id DESC
        LIMIT ? 
        OFFSET ?
    """

    pagination_params = params + [per_page, offset]

    jobs = conn.execute(
        query,
        pagination_params
    ).fetchall()

    # gets the dropdown options, distinct removes duplicates
    # where removes null ie no value exists, not equal to '' value exists as text but contains no characters
    # order by is alphabetical, DESC would be by descending order
    alert_names = conn.execute("""
        SELECT DISTINCT alert_name
        FROM jobs
        WHERE alert_name IS NOT NULL
            AND alert_name != ''
        ORDER BY alert_name;
    """).fetchall()

    companies = conn.execute("""
        SELECT DISTINCT company
        FROM jobs
        WHERE company IS NOT NULL
            AND company != ''
        ORDER BY company;
    """).fetchall()

    locations = conn.execute("""
            SELECT DISTINCT location
            FROM jobs
            WHERE location IS NOT NULL
                AND location != ''
            ORDER BY location;
    """).fetchall()

    conn.close()

    # renders the html template, alert name sends distinct alert name rows to template so jinja can build dropdown
    # selected alert sends the currently selected alert into the template
    # alert name is python, selected name is html
    return render_template(
        "index.html", 
        jobs=jobs,
        alert_names=alert_names,
        companies=companies,
        locations=locations,
        selected_alert=request_alert_name,
        selected_interested=interested,
        selected_applied=applied,
        selected_company=selected_company,
        selected_location=selected_location,
        page=page,
        total_pages=total_pages,
        total_jobs=total_jobs,
        per_page=per_page
    )

# creates a checkbox in the interested column so that I can multiselect and update in bulk
@app.route("/bulk_update_interested", methods=["POST"])
def bulk_update_interested():
    # get checked ids from checkboxes
    selected_ids = request.form.getlist("selected_jobs")
    page = request.form.get("page", 1, type=int)

    #get value selected in interested drop down
    interested = request.form.get("bulk_interested", "").strip()

    # remember current filter name
    alert_name = request.form.get("alert_name", "")

    # converts clear option to blank db value
    if interested == "Clear":
        interested = ""

    # only allows valid interested values
    allowed_values = {"Yes", "No", "Clear"}

    # if no jobs selected or value is invalid, make no changes to db
    if not selected_ids or interested not in allowed_values:
        return redirect(url_for("index", alert_name=alert_name))

    if interested == "Clear":
        interested = ""

    # create one SQL placeholder for every selected job id
    placeholders = ",".join("?" for _ in selected_ids)

    conn = sqlite3.connect("jobs.db")

    conn.execute(
        f"""
        UPDATE jobs
        SET interested = ?
        WHERE id IN ({placeholders});
        """,
        [interested, *selected_ids]
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index", 
            alert_name=alert_name,
            page=page
        )
    )

# if post request is sent to update instersted, run function. number will change depending on row (job id) uses int:job_id
# browser submits update_interested/1, flask extracts job_id = 1, route changes data in the database so flask uses POST request
# get is default, POST needs to be called out... get - give, post - send
@app.route("/update_interested/<int:job_id>", methods=["POST"])
# job_id is automatically passed into the function based on the URL containing int:job_id
def update_interested(job_id):

    # request form reads info that is in the html form, ie selecting yes for interested
    interested = request.form.get("interested")
    page = request.form.get("page", 1, type=int)

    # this remembers what filter is selected for alert name
    alert_name = request.form.get("alert_name", "")

    conn = sqlite3.connect("jobs.db")

    # SQL code that modifies data.. update jobs table, set changes the interested column, where for the specific row
    # interested is from the form, job_id is from the int:job_id, python then supplies interested and job id
    conn.execute("""
        UPDATE jobs
        SET interested = ?
        WHERE id = ?;
    """, (interested, job_id)
    )

    # conn.commit is saving to the database, basically like clicking the save button
    conn.commit()
    conn.close()

    # flask asks what url belongs to index (/), if alertname is included (build /?alert_name=Power BI)
    # then redirect tells browser to load that page
    return redirect(
        url_for(
            "index", 
            alert_name=alert_name,
            page=page
        )
    )

@app.route("/update_applied/<int:job_id>", methods=["POST"])
def update_applied(job_id):
    applied = request.form.get("applied")
    alert_name = request.form.get("alert_name", "")
    page = request.form.get("page", 1, type=int)

    conn = sqlite3.connect("jobs.db")

    conn.execute("""
        UPDATE jobs
        SET applied = ?
        WHERE id = ?;
    """, (applied, job_id)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index", 
            alert_name=alert_name,
            page=page
        )
    )

@app.route("/update_interview/<int:job_id>", methods=["POST"])
def update_interview(job_id):
    interview = request.form.get("interview")
    alert_name = request.form.get("alert_name", "")
    page = request.form.get("page", 1, type=int)

    conn = sqlite3.connect("jobs.db")

    conn.execute("""
        UPDATE jobs
        SET interview = ?
        WHERE id = ?;
    """, (interview, job_id)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index", 
            alert_name=alert_name,
            page=page
        )
    )

@app.route("/update_posting_status/<int:job_id>", methods=["POST"])
def update_posting_status(job_id):
    posting_status = request.form.get("posting_status")
    alert_name = request.form.get("alert_name", "")
    page = request.form.get("page", 1, type=int)

    conn = sqlite3.connect("jobs.db")

    conn.execute("""
        UPDATE jobs
        SET posting_status = ?
        WHERE id = ?;
    """, (posting_status, job_id)
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index", 
            alert_name=alert_name,
            page=page
        )
    )

@app.route("/archive_reviewed", methods=["POST"])
def archive_reviewed():

    conn = sqlite3.connect("jobs.db")

    conn.execute("""
        UPDATE jobs
        SET is_archived = 1
        WHERE is_archived = 0
            AND (
                interested = 'No'
                OR posting_status = 'Closed'
            );
    """
    )

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "index"
        )
    )

@app.route("/companies")
def companies():
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row

    company_search = request.args.get("company_search", "").strip()
    where_clause = ""
    params = []

    if company_search:
        where_clause = "WHERE company LIKE ?"
        params.append(f"%{company_search}%")

    companies = conn.execute("""
        SELECT 
            id,
            company,
            favorite
        FROM companies
    """ + where_clause + """
        ORDER BY 
            favorite DESC,
            company ASC;
    """, params
    ).fetchall()

    conn.close()

    return render_template(
        "companies.html",
        companies=companies,
        company_search=company_search
    )

@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row

    company = conn.execute("""
        SELECT 
            companies.id,
            companies.company,
            companies.favorite,
            company_detail.website,
            company_detail.notes,
            company_detail.referrals
        FROM companies
        LEFT JOIN company_detail
            ON companies.id = company_detail.company_id
        WHERE companies.id = ?;
    """, (company_id,)).fetchone()

    conn.close()

    return render_template(
        "company_detail.html",
        company=company
    )

@app.route("/companies/<int:company_id>/details", methods=["POST"])
def update_company_detail(company_id):
    conn = sqlite3.connect("jobs.db")
    conn.row_factory = sqlite3.Row

    website = request.form.get("website", "")
    notes = request.form.get("notes", "")
    referrals = request.form.get("referrals", "")

    company_exists = conn.execute("""
        SELECT 
            id
        FROM company_detail
        WHERE company_id = ?
        ;
    """, (company_id,)).fetchone()

    if company_exists:
        conn.execute(
        """
            UPDATE company_detail
            SET website = ?,
                notes = ?,
                referrals = ?
            WHERE company_id = ?;
        """, (website, notes, referrals, company_id))
    else:
        conn.execute(
        """
            INSERT INTO company_detail
            (
                company_id,
                website,
                notes,
                referrals
            )
            VALUES
            (?, ?, ?, ?)
        """, (company_id, website, notes, referrals))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "company_detail", 
            company_id=company_id,
        )
    )

@app.route("/companies/<int:company_id>/favorite", methods=["POST"])
def toggle_company_favorite(company_id):
    conn = sqlite3.connect("jobs.db")

    conn.execute("""
        UPDATE companies
        SET favorite = 
            CASE
                WHEN favorite = 1 THEN 0
                ELSE 1
            END
        WHERE id = ?;
    """, (company_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("companies"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
