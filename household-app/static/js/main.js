async function loadItems(section) {
    const res = await fetch(`/api/${section}`);
    const items = await res.json();
    const list = document.getElementById(`${section}-list`);
    list.innerHTML = "";
    items.forEach(item => list.appendChild(renderItem(section, item)));
}

function renderItem(section, item) {
    const li = document.createElement("li");
    if (item.done) li.classList.add("done");

    const span = document.createElement("span");
    span.textContent = item.text;
    span.onclick = () => toggleItem(section, item.id);

    const del = document.createElement("button");
    del.textContent = "x";
    del.className = "delete-btn";
    del.onclick = () => deleteItem(section, item.id);

    li.appendChild(span);
    li.appendChild(del);
    return li;
}

async function addItem(section, inputId) {
    const input = document.getElementById(inputId);
    const text = input.value.trim();
    if (!text) return;
    await fetch(`/api/${section}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    });
    input.value = "";
    loadItems(section);
}

async function toggleItem(section, id) {
    await fetch(`/api/${section}/${id}`, { method: "PATCH" });
    loadItems(section);
}

async function deleteItem(section, id) {
    await fetch(`/api/${section}/${id}`, { method: "DELETE" });
    loadItems(section);
}

document.addEventListener("DOMContentLoaded", () => {
    loadItems("todos");
    loadItems("groceries");
});

document.getElementById("todo-input").addEventListener("keydown", e => {
    if (e.key === "Enter") addItem("todos", "todo-input");
});
document.getElementById("grocery-input").addEventListener("keydown", e => {
    if (e.key === "Enter") addItem("groceries", "grocery-input");
});
