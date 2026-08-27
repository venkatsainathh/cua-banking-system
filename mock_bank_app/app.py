import asyncio
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Legacy Core Banking Stand-in")

MOCK_MEMBERS = {
    "12345": {"name": "Alice Johnson", "status": "ACTIVE", "savings_balance": 15420.50},
    "67890": {"name": "Bob Smith", "status": "LOCKED", "savings_balance": 250.00},
}

BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Core Banking Portal - Backoffice 2008</title>
    <style>
        body {{ font-family: monospace; background: #e0e0e0; padding: 20px; }}
        .window {{ background: #fff; border: 2px solid #555; padding: 15px; width: 700px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        td, th {{ border: 1px solid #999; padding: 6px; text-align: left; }}
        .header {{ background: #003366; color: white; padding: 8px; font-weight: bold; }}
        .btn {{ background: #ccc; border: 2px outset #fff; padding: 4px 10px; cursor: pointer; }}
        .error {{ color: red; font-weight: bold; }}
        .success {{ color: green; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="window">
        <div class="header">CORE-BANKING ENGINE v4.2.1 [HOST: PRD-US-EAST]</div>
        <div style="padding: 10px 0;">{content}</div>
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    content = """
    <form action="/member/search" method="post">
        <table>
            <tr><th colspan="2">Member Lookup Subsystem</th></tr>
            <tr>
                <td><label for="f_mem_id">Member Account ID:</label></td>
                <td><input type="text" id="f_mem_id" name="member_id" autocomplete="off" /></td>
            </tr>
            <tr>
                <td colspan="2"><input class="btn" type="submit" value="Query Database" /></td>
            </tr>
        </table>
    </form>
    """
    return BASE_HTML.format(content=content)

@app.post("/member/search", response_class=HTMLResponse)
async def search_member(member_id: str = Form(...)):
    if member_id not in MOCK_MEMBERS:
        content = f"""
        <div class="error" id="msg_banner">BUSINESS EXCEPTION: Record not found for Member ID [{member_id}]</div>
        <br/><a href="/" class="btn">Back to Query</a>
        """
        return BASE_HTML.format(content=content)

    member = MOCK_MEMBERS[member_id]
    if member["status"] == "LOCKED":
        content = f"""
        <div class="error" id="msg_banner">PERMISSION DENIAL: Member account status is LOCKED. Servicing prohibited.</div>
        <br/><a href="/" class="btn">Back to Query</a>
        """
        return BASE_HTML.format(content=content)

    content = f"""
    <div id="member_record">
        <h3>Member Profile: <span id="val_name">{member['name']}</span></h3>
        <table>
            <tr><td>Account Status</td><td id="val_status">{member['status']}</td></tr>
            <tr><td>Primary Savings Balance</td><td id="val_balance">${member['savings_balance']:,.2f}</td></tr>
        </table>
        <br/>
        <form action="/account/new" method="get">
            <input type="hidden" name="member_id" value="{member_id}" />
            <input class="btn" type="submit" value="Open Sub-Account" />
        </form>
    </div>
    """
    return BASE_HTML.format(content=content)

@app.get("/account/new", response_class=HTMLResponse)
async def new_account_form(member_id: str):
    content = f"""
    <h3>Sub-Account Creation Module</h3>
    <form action="/account/create" method="post">
        <input type="hidden" name="member_id" value="{member_id}" />
        <table>
            <tr>
                <td>Target Product:</td>
                <td>
                    <select name="product_type" id="sel_prod">
                        <option value="MONEY_MARKET">High Yield Money Market (4.50% APY)</option>
                        <option value="CD_12M">12-Month Certificate of Deposit (5.10% APY)</option>
                    </select>
                </td>
            </tr>
            <tr>
                <td>Initial Deposit ($):</td>
                <td><input type="text" name="initial_deposit" id="txt_deposit" value="500.00" /></td>
            </tr>
            <tr>
                <td colspan="2"><input class="btn" type="submit" value="Submit & Authorize" /></td>
            </tr>
        </table>
    </form>
    """
    return BASE_HTML.format(content=content)

@app.post("/account/create", response_class=HTMLResponse)
async def create_account(member_id: str = Form(...), product_type: str = Form(...), initial_deposit: str = Form(...)):
    await asyncio.sleep(0.3)
    confirmation_no = f"CONF-{member_id}-99281"
    content = f"""
    <div id="confirmation_screen">
        <div class="success" id="confirmation_header">SUB-ACCOUNT CREATION AUTHORIZED</div>
        <table>
            <tr><td>Confirmation Number:</td><td id="val_conf_no">{confirmation_no}</td></tr>
            <tr><td>Member Ref:</td><td>{member_id}</td></tr>
            <tr><td>Product Assigned:</td><td id="val_product">{product_type}</td></tr>
            <tr><td>Funded Amount:</td><td id="val_amount">${initial_deposit}</td></tr>
        </table>
        <br/><a href="/" class="btn">Return to Console</a>
    </div>
    """
    return BASE_HTML.format(content=content)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)