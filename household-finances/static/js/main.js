let incomeChart = null;
let expenseChart = null;
let balanceChart = null;

const COLORS = [
    "#4f46e5", "#e53e3e", "#38a169", "#d69e2e",
    "#3182ce", "#805ad5", "#dd6b20", "#319795"
];

function currentMonth() {
    return document.getElementById("month-picker").value;
}

function fmt(n) {
    return "$" + parseFloat(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function loadAll() {
    const month = currentMonth();
    await Promise.all([loadSummary(month), loadIncomes(month), loadExpenses(month)]);
}

async function loadSummary(month) {
    const url = month ? `/api/summary?month=${month}` : "/api/summary";
    const res = await fetch(url);
    const data = await res.json();

    document.getElementById("total-income").textContent = fmt(data.total_income);
    document.getElementById("total-expenses").textContent = fmt(data.total_expenses);
    const balEl = document.getElementById("balance");
    balEl.textContent = fmt(data.balance);
    balEl.className = "card-value " + (data.balance >= 0 ? "positive" : "negative");

    renderIncomeChart(data.incomes_by_person);
    renderExpenseChart(data.expenses_by_category);
    renderBalanceChart(data.total_income, data.total_expenses);
}

function renderIncomeChart(data) {
    const ctx = document.getElementById("income-chart").getContext("2d");
    if (incomeChart) incomeChart.destroy();
    incomeChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.map(d => d.person),
            datasets: [{
                data: data.map(d => parseFloat(d.total)),
                backgroundColor: COLORS
            }]
        },
        options: { plugins: { legend: { position: "bottom" } } }
    });
}

function renderExpenseChart(data) {
    const ctx = document.getElementById("expense-chart").getContext("2d");
    if (expenseChart) expenseChart.destroy();
    expenseChart = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: data.map(d => d.category),
            datasets: [{
                data: data.map(d => parseFloat(d.total)),
                backgroundColor: COLORS
            }]
        },
        options: { plugins: { legend: { position: "bottom" } } }
    });
}

function renderBalanceChart(income, expenses) {
    const ctx = document.getElementById("balance-chart").getContext("2d");
    if (balanceChart) balanceChart.destroy();
    balanceChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Income", "Expenses"],
            datasets: [{
                data: [income, expenses],
                backgroundColor: ["#38a169", "#e53e3e"]
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });
}

async function loadIncomes(month) {
    const url = month ? `/api/incomes?month=${month}` : "/api/incomes";
    const res = await fetch(url);
    const items = await res.json();
    const list = document.getElementById("incomes-list");
    list.innerHTML = "";
    items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span class="entry-label">${item.person}</span>
            <span class="entry-sub">${item.month}</span>
            <span class="entry-amount">${fmt(item.amount)}</span>
            <button class="delete-btn" onclick="deleteIncome(${item.id})">x</button>
        `;
        list.appendChild(li);
    });
}

async function loadExpenses(month) {
    const url = month ? `/api/expenses?month=${month}` : "/api/expenses";
    const res = await fetch(url);
    const items = await res.json();
    const list = document.getElementById("expenses-list");
    list.innerHTML = "";
    items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = `
            <span class="entry-label">${item.category}</span>
            <span class="entry-sub">${item.description || ""} &bull; ${item.month}</span>
            <span class="entry-amount">${fmt(item.amount)}</span>
            <button class="delete-btn" onclick="deleteExpense(${item.id})">x</button>
        `;
        list.appendChild(li);
    });
}

async function addIncome() {
    const person = document.getElementById("income-person").value.trim();
    const amount = parseFloat(document.getElementById("income-amount").value);
    const month = document.getElementById("income-month").value;
    if (!person || !amount || !month) return;
    await fetch("/api/incomes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ person, amount, month })
    });
    document.getElementById("income-person").value = "";
    document.getElementById("income-amount").value = "";
    loadAll();
}

async function addExpense() {
    const category = document.getElementById("expense-category").value.trim();
    const description = document.getElementById("expense-description").value.trim();
    const amount = parseFloat(document.getElementById("expense-amount").value);
    const month = document.getElementById("expense-month").value;
    if (!category || !amount || !month) return;
    await fetch("/api/expenses", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, description, amount, month })
    });
    document.getElementById("expense-category").value = "";
    document.getElementById("expense-description").value = "";
    document.getElementById("expense-amount").value = "";
    loadAll();
}

async function deleteIncome(id) {
    await fetch(`/api/incomes/${id}`, { method: "DELETE" });
    loadAll();
}

async function deleteExpense(id) {
    await fetch(`/api/expenses/${id}`, { method: "DELETE" });
    loadAll();
}

document.addEventListener("DOMContentLoaded", () => {
    const now = new Date();
    const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
    document.getElementById("month-picker").value = month;
    document.getElementById("income-month").value = month;
    document.getElementById("expense-month").value = month;
    loadAll();
});
