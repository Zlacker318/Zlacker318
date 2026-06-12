let dragSrc = null;

async function loadItems(section) {
    const res = await fetch(`/api/${section}`);
    const items = await res.json();
    const list = document.getElementById(`${section}-list`);
    list.innerHTML = "";
    items.forEach(item => list.appendChild(renderItem(section, item)));
}

function renderItem(section, item) {
    const li = document.createElement("li");
    li.dataset.id = item.id;
    if (item.done) li.classList.add("done");
    li.draggable = true;

    const grip = document.createElement("span");
    grip.className = "grip";
    grip.textContent = "⠿";

    const span = document.createElement("span");
    span.textContent = item.text;
    span.onclick = () => toggleItem(section, item.id);

    const del = document.createElement("button");
    del.textContent = "x";
    del.className = "delete-btn";
    del.onclick = () => deleteItem(section, item.id);

    li.appendChild(grip);
    li.appendChild(span);
    li.appendChild(del);

    li.addEventListener("dragstart", e => {
        dragSrc = li;
        e.dataTransfer.effectAllowed = "move";
        setTimeout(() => li.classList.add("dragging"), 0);
    });

    li.addEventListener("dragend", () => {
        li.classList.remove("dragging");
        document.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));
    });

    li.addEventListener("dragover", e => {
        e.preventDefault();
        e.dataTransfer.dropEffect = "move";
        if (dragSrc && dragSrc !== li) {
            document.querySelectorAll(".drag-over").forEach(el => el.classList.remove("drag-over"));
            li.classList.add("drag-over");
        }
    });

    li.addEventListener("drop", e => {
        e.preventDefault();
        li.classList.remove("drag-over");
        if (!dragSrc || dragSrc === li) return;
        const list = li.parentNode;
        const items = [...list.querySelectorAll("li")];
        const srcIdx = items.indexOf(dragSrc);
        const dstIdx = items.indexOf(li);
        if (srcIdx < dstIdx) {
            list.insertBefore(dragSrc, li.nextSibling);
        } else {
            list.insertBefore(dragSrc, li);
        }
        syncOrder(section, list);
    });

    return li;
}

async function syncOrder(section, list) {
    const ids = [...list.querySelectorAll("li")].map(li => parseInt(li.dataset.id));
    await fetch(`/api/${section}/reorder`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids })
    });
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
