const state = {
  workOrder: null,
  tasks: [],
  controls: [],
  hazards: [],
  riskCategories: [],
  personnel: [], // Store personnel at risk options
  controlSelection: new Set(),
  hazardSelection: new Set(),
  controlParameterValues: new Map(), // Store parameter values by control ID
  riskSelection: { likelihood: 1, severity: 1 },
  activeTaskId: null,
  activeHazardId: null,
  activeControlPhase: null,
  activeRiskContext: null,
};

const ControlPhase = {
  EXISTING: "existing",
  ADDITIONAL: "additional",
};

const hazardModalEl = document.getElementById("hazardModal");
const controlModalEl = document.getElementById("controlModal");
const personnelModalEl = document.getElementById("personnelModal");
const hazardModal = hazardModalEl ? new bootstrap.Modal(hazardModalEl) : null;
const controlModal = controlModalEl ? new bootstrap.Modal(controlModalEl) : null;
const personnelModal = personnelModalEl ? new bootstrap.Modal(personnelModalEl) : null;

const hazardOptionsEl = document.getElementById("hazardOptions");
const hazardSearchEl = document.getElementById("hazardSearch");
const hazardModalSaveBtn = document.getElementById("hazardModalSave");

const controlOptionsEl = document.getElementById("controlOptions");
const controlSearchEl = document.getElementById("controlSearch");
const controlModalSaveBtn = document.getElementById("controlModalSave");
const controlModalTitleEl = document.getElementById("controlModalTitle");
const selectedControlsEl = document.getElementById("selectedControls");

const personnelOptionsEl = document.getElementById("personnelOptions");
const personnelModalSaveBtn = document.getElementById("personnelModalSave");
const selectedPersonnelEl = document.getElementById("selectedPersonnel");
const controlPhaseLabelEl = document.getElementById("controlPhaseLabel");

const riskModalEl = document.getElementById("riskModal");
const riskModal = riskModalEl ? new bootstrap.Modal(riskModalEl) : null;
const riskMatrixGrid = document.getElementById("riskMatrixGrid");
const riskModalSaveBtn = document.getElementById("riskModalSave");
const riskModalTitleEl = document.getElementById("riskModalTitle");
const riskSelectedLabelEl = document.getElementById("riskSelectedLabel");
const riskSelectedLikelihoodEl = document.getElementById("riskSelectedLikelihood");
const riskSelectedSeverityEl = document.getElementById("riskSelectedSeverity");

const taskTableBody = document.getElementById("taskTableBody");
const addTaskBtn = document.getElementById("addTask");
const loadWorkOrderBtn = document.getElementById("loadWorkOrder");
const importSampleBtn = document.getElementById("importSample");
const importUploadedBtn = document.getElementById("importUploaded");
const messageArea = document.getElementById("messageArea");

const likelihoodOptions = [1, 2, 3, 4, 5];

async function loadInitialData() {
  try {
    const [controlsResponse, hazardsResponse, riskCategoriesResponse, personnelResponse] = await Promise.all([
      fetchJSON("/api/catalog/controls"),
      fetchJSON("/api/catalog/hazards"),
      fetchJSON("/api/risk-matrix"),
      fetchJSON("/api/catalog/personnel"),
    ]);

    state.controls = controlsResponse.controls || [];
    state.hazards = hazardsResponse.hazards || [];
    state.riskCategories = riskCategoriesResponse.risk_categories || [];
    state.personnel = personnelResponse.personnel || [];

    console.log("Initial data loaded:", {
      controls: state.controls.length,
      hazards: state.hazards.length,
      riskCategories: state.riskCategories.length,
      personnel: state.personnel.length,
    });
  } catch (error) {
    console.error("Failed to load initial data:", error);
    flashMessage("Failed to load application data", "danger");
  }
}

async function init() {
  try {
    await loadInitialData();
    attachEventHandlers();
  } catch (error) {
    flashMessage(`Failed to load reference data: ${error.message}`, "danger");
  }
}

function attachEventHandlers() {
  if (addTaskBtn) {
    addTaskBtn.addEventListener("click", handleAddTask);
  }
  if (loadWorkOrderBtn) {
    loadWorkOrderBtn.addEventListener("click", handleLoadWorkOrder);
  }
  if (importSampleBtn) {
    importSampleBtn.addEventListener("click", handleImportSample);
  }
  if (importUploadedBtn) {
    importUploadedBtn.addEventListener("click", handleImportUploaded);
  }
  if (taskTableBody) {
    taskTableBody.addEventListener("change", handleFieldChange);
    taskTableBody.addEventListener("click", handleTableClick);
  }
  if (hazardSearchEl) {
    hazardSearchEl.addEventListener("input", () => renderHazardOptions(hazardSearchEl.value));
  }
  if (hazardModalSaveBtn) {
    hazardModalSaveBtn.addEventListener("click", handleHazardModalSave);
  }
  if (controlSearchEl) {
    controlSearchEl.addEventListener("input", () => renderControlOptions(controlSearchEl.value));
  }
  if (controlModalSaveBtn) {
    controlModalSaveBtn.addEventListener("click", handleControlModalSave);
  }
  if (personnelModalSaveBtn) {
    personnelModalSaveBtn.addEventListener("click", handlePersonnelModalSave);
  }
  if (riskModalSaveBtn) {
    riskModalSaveBtn.addEventListener("click", handleRiskModalSave);
  }
  if (riskModalEl) {
    riskModalEl.addEventListener("hidden.bs.modal", resetRiskModal);
  }
  
  // Auto-resize all textareas on page load
  document.querySelectorAll('textarea.js-field').forEach(autoResizeTextarea);
}

function getWorkOrderInputs() {
  const woNumberEl = document.getElementById("woNumber");
  const woTitleEl = document.getElementById("woTitle");
  return {
    woNumber: woNumberEl?.value?.trim() || "",
    title: woTitleEl?.value?.trim() || ""
  };
}

async function handleLoadWorkOrder() {
  const { woNumber } = getWorkOrderInputs();
  if (!woNumber) {
    flashMessage("Enter a work order number first.", "warning");
    return;
  }
  try {
    const data = await fetchJSON(`/api/work-orders/${encodeURIComponent(woNumber)}`);
    state.workOrder = data.work_order;
    state.tasks = data.tasks ?? [];
    renderTasks();
    flashMessage(`Loaded work order ${woNumber}.`, "success");
  } catch (error) {
    flashMessage(`Unable to load work order: ${error.message}`, "danger");
  }
}

async function handleImportSample() {
  const { woNumber, title } = getWorkOrderInputs();
  if (!woNumber) {
    flashMessage("Enter a work order number to import into.", "warning");
    return;
  }
  try {
    const payload = { filename: "wo1001_pump_overhaul.csv", title, replace: true };
    const data = await fetchJSON(`/api/work-orders/${encodeURIComponent(woNumber)}/import`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.workOrder = data.work_order;
    state.tasks = data.tasks ?? [];
    renderTasks();
    flashMessage(`Imported sample MS into ${woNumber}.`, "success");
  } catch (error) {
    flashMessage(`Import failed: ${error.message}`, "danger");
  }
}

async function handleImportUploaded() {
  const fileInput = document.getElementById("msUpload");
  const { woNumber, title } = getWorkOrderInputs();
  if (!woNumber) {
    flashMessage("Enter a work order number to import into.", "warning");
    return;
  }
  if (!fileInput?.files?.length) {
    flashMessage("Select a CSV file first.", "warning");
    return;
  }
  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);
  if (title) {
    formData.append("title", title);
  }
  formData.append("replace", "true");

  try {
    const response = await fetch(`/api/work-orders/${encodeURIComponent(woNumber)}/import`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    const data = await response.json();
    state.workOrder = data.work_order;
    state.tasks = data.tasks ?? [];
    renderTasks();
    fileInput.value = "";
    flashMessage(`Imported ${file.name} into ${woNumber}.`, "success");
  } catch (error) {
    flashMessage(`Upload failed: ${error.message}`, "danger");
  }
}

async function handleAddTask() {
  if (!state.workOrder) {
    flashMessage("Load or import a work order first.", "warning");
    return;
  }
  try {
    const payload = {
      work_order_number: state.workOrder.number,
      activity: "New activity",
      personnel_at_risk: "",
      existing_controls_summary: "",
      additional_controls_summary: "",
      likelihood: 1,
      severity: 1,
      residual_likelihood: 1,
      residual_severity: 1,
      sequence: state.tasks.length + 1,
    };
    const data = await fetchJSON("/api/tasks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.tasks.push(data.task);
    renderTasks();
  } catch (error) {
    flashMessage(`Unable to add task: ${error.message}`, "danger");
  }
}

function handleFieldChange(event) {
  const target = event.target;
  if (!target.classList.contains("js-field")) {
    return;
  }
  
  // Auto-resize textarea
  if (target.tagName === 'TEXTAREA') {
    autoResizeTextarea(target);
  }
  
  const row = target.closest("tr[data-task-id]");
  if (!row) {
    return;
  }
  const taskId = parseInt(row.dataset.taskId, 10);
  const field = target.dataset.field;
  const value = target.value;
  updateTask(taskId, { [field]: value });
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = Math.max(textarea.scrollHeight, 64) + 'px';
}

function handleTableClick(event) {
  const riskButton = event.target.closest(".js-edit-risk");
  if (riskButton) {
    const row = riskButton.closest("tr[data-task-id]");
    if (!row) {
      return;
    }
    const taskId = parseInt(row.dataset.taskId, 10);
    const phase = riskButton.dataset.phase || "initial";
    openRiskModal(taskId, phase);
    return;
  }
  const editHazardBtn = event.target.closest(".js-edit-hazards");
  if (editHazardBtn) {
    const row = editHazardBtn.closest("tr[data-task-id]");
    const taskId = parseInt(row.dataset.taskId, 10);
    openHazardModal(taskId);
    return;
  }
  const editControlBtn = event.target.closest(".js-edit-controls");
  if (editControlBtn) {
    const taskId = parseInt(editControlBtn.closest("tr").dataset.taskId);
    const phase = editControlBtn.dataset.phase;
    const hazardId = editControlBtn.dataset.hazardId ? parseInt(editControlBtn.dataset.hazardId) : null;
    openControlModal(taskId, phase, hazardId);
    return;
  }
  const editPersonnelBtn = event.target.closest(".js-edit-personnel");
  if (editPersonnelBtn) {
    const taskId = parseInt(editPersonnelBtn.dataset.taskId);
    openPersonnelModal(taskId);
    return;
  }
  const deleteBtn = event.target.closest(".js-delete-task");
  if (deleteBtn) {
    const row = deleteBtn.closest("tr[data-task-id]");
    const taskId = parseInt(row.dataset.taskId, 10);
    deleteTask(taskId);
  }
}

async function updateTask(taskId, payload) {
  try {
    const data = await fetchJSON(`/api/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    mergeTask(data.task);
    renderTasks();
  } catch (error) {
    flashMessage(`Update failed: ${error.message}`, "danger");
  }
}

async function deleteTask(taskId) {
  if (!confirm("Remove this task?")) {
    return;
  }
  try {
    const response = await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
    if (!response.ok) {
      throw new Error(await response.text());
    }
    state.tasks = state.tasks.filter((task) => task.id !== taskId);
    renderTasks();
  } catch (error) {
    flashMessage(`Delete failed: ${error.message}`, "danger");
  }
}

function renderTasks() {
  if (!taskTableBody) {
    return;
  }
  taskTableBody.innerHTML = "";
  if (!state.tasks.length) {
    const row = document.createElement("tr");
    row.className = "placeholder-row";
    row.innerHTML = '<td colspan="9" class="text-center py-5 text-muted">No tasks yet. Import a method statement or add tasks.</td>';
    taskTableBody.appendChild(row);
    if (state.workOrder) {
      addTaskBtn?.removeAttribute("disabled");
    }
    return;
  }
  addTaskBtn?.removeAttribute("disabled");
  state.tasks
    .slice()
    .sort((a, b) => (a.sequence ?? 0) - (b.sequence ?? 0))
    .forEach((task) => {
      renderTaskRows(task);
    });
  
  // Auto-resize all textareas after rendering
  setTimeout(() => {
    document.querySelectorAll('textarea.js-field').forEach(autoResizeTextarea);
  }, 0);
}

function renderTaskRows(task) {
  if (!task.hazards || task.hazards.length === 0) {
    // Task with no hazards - single row
    const row = document.createElement("tr");
    row.dataset.taskId = task.id;
    row.innerHTML = renderTaskRowWithoutHazards(task);
    taskTableBody.appendChild(row);
  } else {
    // Task with hazards - multiple rows
    task.hazards.forEach((hazard, index) => {
      const row = document.createElement("tr");
      row.dataset.taskId = task.id;
      row.dataset.hazardId = hazard.id;
      row.innerHTML = renderTaskRowWithHazard(task, hazard, index);
      taskTableBody.appendChild(row);
    });
  }
}

function renderTaskRow(task) {
  return `
    <td rowspan="${Math.max(task.hazards?.length || 1, 1)}">
      <textarea class="form-control form-control-sm js-field" data-field="activity">${escapeHTML(task.activity ?? "")}</textarea>
    </td>
    ${renderHazardRows(task)}
    <td rowspan="${Math.max(task.hazards?.length || 1, 1)}">
      <textarea class="form-control form-control-sm js-field" data-field="personnel_at_risk">${escapeHTML(task.personnel_at_risk ?? "")}</textarea>
    </td>
    ${renderRiskCell(task, "initial").replace('<td', `<td rowspan="${Math.max(task.hazards?.length || 1, 1)}"`)}
    <td rowspan="${Math.max(task.hazards?.length || 1, 1)}">
      <input type="date" class="form-control form-control-sm js-field" data-field="target_completion_date" value="${task.target_completion_date ?? ""}">
    </td>
    ${renderRiskCell(task, "residual").replace('<td', `<td rowspan="${Math.max(task.hazards?.length || 1, 1)}"`)}
    <td rowspan="${Math.max(task.hazards?.length || 1, 1)}" class="text-center">
      <button type="button" class="btn btn-sm js-delete-task" title="Delete task" style="border: none; background: none; padding: 2px;">
        <i class="fa-solid fa-trash" style="color: #ff3d3d;"></i>
      </button>
    </td>
  `;
}

function renderHazardRows(task) {
  if (!task.hazards || task.hazards.length === 0) {
    return `
      <td>
        <button type="button" class="btn btn-link btn-sm js-edit-hazards">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i> Select hazards
        </button>
      </td>
      <td>
        <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="existing" data-hazard-id="">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i> Select controls
        </button>
      </td>
      <td>
        <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="additional" data-hazard-id="">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i> Select controls
        </button>
      </td>
    `;
  }

  return task.hazards.map((hazard, index) => {
    const hazardCell = index === 0 ? `
      <td rowspan="${task.hazards.length}">
        <div class="cell-badges mb-1">${renderHazardBadges(task.hazards)}</div>
        <button type="button" class="btn btn-link btn-sm js-edit-hazards">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i> Select hazards
        </button>
      </td>
    ` : '';
    
    return `
      ${hazardCell}
      <td>
        <div class="mb-2">
          <strong>${escapeHTML(hazard.name)}</strong>
          ${hazard.parameter_value ? `<small class="ms-1 text-muted">(${escapeHTML(hazard.parameter_value)})</small>` : ''}
        </div>
        <div class="cell-badges mb-1">${renderControlBadges(hazard.controls?.existing ?? [])}</div>
        <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="existing" data-hazard-id="${hazard.id}" title="Select controls">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
        </button>
      </td>
      <td>
        <div class="cell-badges mb-1">${renderControlBadges(hazard.controls?.additional ?? [])}</div>
        <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="additional" data-hazard-id="${hazard.id}" title="Select controls">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
        </button>
      </td>
    `;
  }).join('');
}

function renderTaskRowWithoutHazards(task) {
  return `
    <td class="text-center" style="width: 20px; padding: 1px; min-width: 20px;">
      <button type="button" class="btn btn-sm js-delete-task" title="Delete task" style="border: none; background: none; padding: 2px;">
        <i class="fa-solid fa-trash" style="color: #ff3d3d;"></i>
      </button>
    </td>
    <td class="col-activity">
      <textarea class="form-control form-control-sm js-field" data-field="activity">${escapeHTML(task.activity ?? "")}</textarea>
    </td>
    <td>
      <button type="button" class="btn btn-link btn-sm js-edit-hazards" title="Select hazards">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>
    </td>
    <td>
      <div class="d-flex flex-column gap-1">
        <div class="personnel-badges">
          ${renderPersonnelBadges(task.personnel_at_risk || '')}
        </div>
        <button type="button" class="btn btn-link btn-sm js-edit-personnel" data-task-id="${task.id}" title="Select personnel">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
        </button>
      </div>
    </td>
    <td>
      <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="existing" data-hazard-id="" title="Select controls">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>
    </td>
    ${renderRiskCell(task, "initial")}
    <td>
      <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="additional" data-hazard-id="" title="Select controls">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>
    </td>
    <td>
      <input type="date" class="form-control form-control-sm js-field" data-field="target_completion_date" value="${task.target_completion_date ?? ""}">
    </td>
    ${renderRiskCell(task, "residual")}
  `;
}

function renderTaskRowWithHazard(task, hazard, index) {
  const isFirstHazard = index === 0;
  const hazardCount = task.hazards.length;
  
  return `
    ${isFirstHazard ? `<td class="text-center" style="width: 20px; padding: 1px; min-width: 20px;" rowspan="${hazardCount}">
      <button type="button" class="btn btn-sm js-delete-task" title="Delete task" style="border: none; background: none; padding: 2px;">
        <i class="fa-solid fa-trash" style="color: #ff3d3d;"></i>
      </button>
    </td>` : ''}
    ${isFirstHazard ? `<td class="col-activity" rowspan="${hazardCount}">
      <textarea class="form-control form-control-sm js-field" data-field="activity">${escapeHTML(task.activity ?? "")}</textarea>
    </td>` : ''}
    <td>
      <div class="mb-2">
        <strong>${escapeHTML(hazard.name)}</strong>
        ${hazard.parameter_value ? `<small class="ms-1 text-muted">(${escapeHTML(hazard.parameter_value)})</small>` : ''}
      </div>
      ${isFirstHazard ? `<button type="button" class="btn btn-link btn-sm js-edit-hazards" title="Edit hazards">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>` : ''}
    </td>
    ${isFirstHazard ? `<td rowspan="${hazardCount}">
      <div class="d-flex flex-column gap-1">
        <div class="personnel-badges">
          ${renderPersonnelBadges(task.personnel_at_risk || '')}
        </div>
        <button type="button" class="btn btn-link btn-sm js-edit-personnel" data-task-id="${task.id}" title="Select personnel">
          <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
        </button>
      </div>
    </td>` : ''}
    <td>
      <div class="cell-badges mb-1">${renderControlBadges(hazard.controls?.existing ?? [])}</div>
      <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="existing" data-hazard-id="${hazard.id}" title="Select controls">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>
    </td>
    ${isFirstHazard ? renderRiskCell(task, "initial").replace('<td', `<td rowspan="${hazardCount}"`) : ''}
    <td>
      <div class="cell-badges mb-1">${renderControlBadges(hazard.controls?.additional ?? [])}</div>
      <button type="button" class="btn btn-link btn-sm js-edit-controls" data-phase="additional" data-hazard-id="${hazard.id}" title="Select controls">
        <i class="bi bi-plus-circle" style="font-size: 0.8rem;"></i>
      </button>
    </td>
    ${isFirstHazard ? `<td rowspan="${hazardCount}">
      <input type="date" class="form-control form-control-sm js-field" data-field="target_completion_date" value="${task.target_completion_date ?? ""}">
    </td>` : ''}
    ${isFirstHazard ? renderRiskCell(task, "residual").replace('<td', `<td rowspan="${hazardCount}"`) : ''}
  `;
}




function renderRiskButton(task, phase) {
  const isResidual = phase === "residual";
  const likelihood = Number(isResidual ? task.residual_likelihood ?? 1 : task.likelihood ?? 1);
  const severity = Number(isResidual ? task.residual_severity ?? 1 : task.severity ?? 1);
  const rawScore = isResidual ? task.residual_risk_score : task.risk_score;
  const score = Number(rawScore ?? likelihood * severity);
  const category = isResidual ? task.residual_risk_category : task.risk_category;
  const hasHazards = task.hazards && task.hazards.length > 0;
  
  let label, fullDescriptor, color, textColor;
  
  if (!hasHazards) {
    // No hazards selected - show evaluate icon
    label = '⚖️';
    fullDescriptor = 'Select hazards first to evaluate risk';
    color = '#f8f9fa';
    textColor = '#666';
  } else if (category) {
    // Risk evaluated
    label = category.label;
    fullDescriptor = `${category.label} - L${likelihood} × S${severity} = ${score}`;
    color = category.color;
    textColor = '#000';
  } else {
    // Hazards selected but risk not evaluated
    label = '⚖️';
    fullDescriptor = 'Click to evaluate risk';
    color = '#fff3cd';
    textColor = '#856404';
  }
  
  return `<button type="button" class="btn btn-sm js-edit-risk w-100" data-phase="${phase}" style="background: transparent; border: none; color: ${textColor}; font-weight: bold; font-size: ${!hasHazards || !category ? '1.2rem' : '0.875rem'};" title="${escapeHTML(fullDescriptor)}">
    ${escapeHTML(label)}
  </button>`;
}

function renderRiskCell(task, phase) {
  const isResidual = phase === "residual";
  const category = isResidual ? task.residual_risk_category : task.risk_category;
  const hasHazards = task.hazards && task.hazards.length > 0;
  
  let color;
  if (!hasHazards) {
    color = '#f8f9fa';
  } else if (category) {
    color = category.color;
  } else {
    color = '#fff3cd';
  }
  
  return `<td style="background-color: ${color}; text-align: center; padding: 8px;">${renderRiskButton(task, phase)}</td>`;
}

function renderHazardBadges(hazards = []) {
  if (!hazards.length) {
    return '<span class=\"text-muted small\">No hazards selected</span>';
  }
  return hazards
    .map((hazard) => {
      let label = escapeHTML(hazard.name);
      if (hazard.parameter_value) {
        const parameterLabel = escapeHTML(hazard.parameter_label || "Value");
        const parameterUnit = hazard.parameter_unit ? ` ${escapeHTML(hazard.parameter_unit)}` : "";
        label += ` (${parameterLabel}: ${escapeHTML(hazard.parameter_value)}${parameterUnit})`;
      }
      return `<span class=\"badge bg-warning-subtle text-dark border\">${label}</span>`;
    })
    .join("");
}


function renderControlBadges(controls = []) {
  if (!controls.length) {
    return '<span class="text-muted small">No controls selected</span>';
  }
  return controls
    .map((control) => {
      const controlName = escapeHTML(control.name);
      const parameterValue = control.parameter_value ? escapeHTML(control.parameter_value) : '';
      const title = parameterValue ? `${controlName} - ${parameterValue}` : controlName;
      
      return `<span class="badge bg-success-subtle text-dark border" title="${title}">
        ${controlName}
        ${parameterValue ? `<small class="ms-1 text-muted">(${parameterValue})</small>` : ''}
      </span>`;
    })
    .join("");
}

function renderPersonnelBadges(personnelString = '') {
  if (!personnelString || personnelString.trim() === '') {
    return '<span class="text-muted small">No personnel selected</span>';
  }
  
  // Split by comma and clean up
  const personnelList = personnelString.split(',').map(p => p.trim()).filter(p => p);
  
  if (personnelList.length === 0) {
    return '<span class="text-muted small">No personnel selected</span>';
  }
  
  return personnelList
    .map(person => `<span class="badge bg-info-subtle text-dark border">${escapeHTML(person)}</span>`)
    .join(' ');
}

function openRiskModal(taskId, phase = "initial") {
  const task = getTask(taskId);
  if (!task) {
    return;
  }
  const isResidual = phase === "residual";
  const likelihood = Number(isResidual ? task.residual_likelihood ?? 1 : task.likelihood ?? 1);
  const severity = Number(isResidual ? task.residual_severity ?? 1 : task.severity ?? 1);
  state.activeRiskContext = { taskId, phase };
  state.riskSelection = { likelihood, severity };
  if (riskModalTitleEl) {
    riskModalTitleEl.textContent = phase === "residual" ? "Select Residual Risk Level" : "Select Risk Level";
  }
  renderRiskMatrix();
  updateRiskModalSelection();
  riskModal?.show();
}

function renderRiskMatrix() {
  if (!riskMatrixGrid || !state.riskSelection) {
    return;
  }
  const likelihoodValues = [1, 2, 3, 4, 5];
  const severityValues = [1, 2, 3, 4, 5];
  let html = '<table class="risk-matrix-table">';
  html += '<thead><tr><th></th>' + severityValues.map((value) => `<th>Severity ${value}</th>`).join('') + '</tr></thead>';
  html += '<tbody>';
  likelihoodValues.forEach((likelihood) => {
    html += `<tr><th>Likelihood ${likelihood}</th>`;
    severityValues.forEach((severity) => {
      const score = likelihood * severity;
      const category = getRiskCategoryByScore(score);
      const isSelected = state.riskSelection &&
        state.riskSelection.likelihood === likelihood &&
        state.riskSelection.severity === severity;
      const classes = `risk-matrix-cell${isSelected ? ' selected' : ''}`;
      const color = category?.color || '#e0e0e0';
      const label = category ? category.label : 'N/A';
      html += `<td class="${classes}" data-likelihood="${likelihood}" data-severity="${severity}" data-score="${score}" style="background-color: ${color};">` +
        `<div class="score">${score}</div>` +
        `<div class="descriptor">${escapeHTML(label)}</div>` +
        '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  riskMatrixGrid.innerHTML = html;
  riskMatrixGrid.querySelectorAll('.risk-matrix-cell').forEach((cell) => {
    cell.addEventListener('click', handleRiskCellSelect);
  });
}

function handleRiskCellSelect(event) {
  const cell = event.currentTarget;
  const likelihood = Number(cell.dataset.likelihood);
  const severity = Number(cell.dataset.severity);
  state.riskSelection = { likelihood, severity };
  renderRiskMatrix();
  updateRiskModalSelection();
}

function updateRiskModalSelection() {
  if (!state.riskSelection) {
    return;
  }
  const { likelihood, severity } = state.riskSelection;
  const score = likelihood * severity;
  if (riskSelectedLikelihoodEl) {
    riskSelectedLikelihoodEl.textContent = likelihood;
  }
  if (riskSelectedSeverityEl) {
    riskSelectedSeverityEl.textContent = severity;
  }
  const category = getRiskCategoryByScore(score);
  if (riskSelectedLabelEl) {
    riskSelectedLabelEl.textContent = category ? `${category.label} (${score})` : `Score ${score}`;
  }
}

function getRiskCategoryByScore(score) {
  return state.riskCategories.find((cat) => score >= cat.min_score && score <= cat.max_score) || null;
}

function resetRiskModal() {
  state.activeRiskContext = null;
  state.riskSelection = null;
  if (riskMatrixGrid) {
    riskMatrixGrid.innerHTML = '';
  }
  if (riskSelectedLabelEl) {
    riskSelectedLabelEl.textContent = 'Current selection: -';
  }
  if (riskSelectedLikelihoodEl) {
    riskSelectedLikelihoodEl.textContent = '-';
  }
  if (riskSelectedSeverityEl) {
    riskSelectedSeverityEl.textContent = '-';
  }
}

async function handleRiskModalSave() {
  if (!state.activeRiskContext || !state.riskSelection) {
    return;
  }
  const { taskId, phase } = state.activeRiskContext;
  const { likelihood, severity } = state.riskSelection;
  const payload = phase === "residual"
    ? { residual_likelihood: likelihood, residual_severity: severity }
    : { likelihood, severity };
  await updateTask(taskId, payload);
  riskModal?.hide();
  resetRiskModal();
}

function openHazardModal(taskId) {
  state.activeTaskId = taskId;
  const currentHazards = getTask(taskId)?.hazards ?? [];
  state.hazardSelection = new Map(
    currentHazards.map((hazard) => [hazard.id, { id: hazard.id, parameter_value: hazard.parameter_value || "" }]),
  );
  hazardSearchEl.value = "";
  renderSelectedHazards();
  renderHazardOptions("");
  hazardModal?.show();
}

function renderSelectedHazards() {
  const selectedHazardsEl = document.getElementById('selectedHazards');
  if (!selectedHazardsEl) return;
  
  if (state.hazardSelection.size === 0) {
    selectedHazardsEl.innerHTML = '';
    return;
  }
  
  const selectedItems = Array.from(state.hazardSelection.values()).map(selection => {
    const hazard = state.hazards.find(h => h.id === selection.id);
    if (!hazard) return '';
    
    let label = hazard.name;
    if (selection.parameter_value) {
      label += ` (${selection.parameter_value})`;
    }
    
    return `<span class="badge bg-primary me-2 mb-2">
      ${escapeHTML(label)}
      <button type="button" class="btn-close btn-close-white ms-1" data-hazard-id="${hazard.id}" style="font-size: 0.7em;"></button>
    </span>`;
  }).join('');
  
  selectedHazardsEl.innerHTML = selectedItems ? `<div class="mb-2"><strong>Selected:</strong></div>${selectedItems}` : '';
  
  // Add click handlers for remove buttons
  selectedHazardsEl.querySelectorAll('.btn-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const hazardId = parseInt(e.target.dataset.hazardId);
      state.hazardSelection.delete(hazardId);
      renderSelectedHazards();
      renderHazardOptions(hazardSearchEl?.value || "");
    });
  });
}

function renderHazardOptions(filter = "") {
  if (!hazardOptionsEl) return;
  const term = filter.toLowerCase();
  hazardOptionsEl.innerHTML = "";
  
  // Filter hazards based on search term
  const filteredHazards = state.hazards.filter((hazard) =>
    !term || hazard.name.toLowerCase().includes(term) || hazard.category.toLowerCase().includes(term)
  );

  if (filteredHazards.length === 0) {
    hazardOptionsEl.innerHTML = '<div class="text-muted text-center py-3">No hazards found</div>';
    return;
  }

  // Group hazards by category
  const hazardsByCategory = {};
  filteredHazards.forEach((hazard) => {
    if (!hazardsByCategory[hazard.category]) {
      hazardsByCategory[hazard.category] = [];
    }
    hazardsByCategory[hazard.category].push(hazard);
  });

  // Sort categories
  const sortedCategories = Object.keys(hazardsByCategory).sort();

  sortedCategories.forEach((category, categoryIndex) => {
    const hazards = hazardsByCategory[category];
    
    // Add separator between categories (except for first)
    if (categoryIndex > 0) {
      const separator = document.createElement("div");
      separator.className = "border-top my-2";
      hazardOptionsEl.appendChild(separator);
    }
    
    // Add category header
    const categoryHeader = document.createElement("div");
    categoryHeader.className = "px-3 py-2 bg-light text-dark fw-bold small";
    categoryHeader.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span>${escapeHTML(category)}</span>
        <small class="text-muted">${hazards.length} hazard${hazards.length !== 1 ? 's' : ''}</small>
      </div>
    `;
    hazardOptionsEl.appendChild(categoryHeader);

    // Add hazards in this category
    hazards.forEach((hazard) => {
      const selection = state.hazardSelection.get(hazard.id);
      const isChecked = Boolean(selection);
      const parameterValue = selection?.parameter_value ?? "";
      const item = document.createElement("label");
      item.className = "list-group-item border-0 d-flex flex-column gap-1";
      const description = hazard.description ? ` - ${escapeHTML(hazard.description)}` : "";
      const parameterMarkup = hazard.requires_parameter
        ? `<div class="mt-1 ms-4 w-100">
            <label class="form-label small mb-1" for="hazard-parameter-${hazard.id}">${escapeHTML(hazard.parameter_label || "Parameter")}${hazard.parameter_unit ? ` (${escapeHTML(hazard.parameter_unit)})` : ""}</label>
            <input type="text" class="form-control form-control-sm js-hazard-parameter" id="hazard-parameter-${hazard.id}" data-hazard-id="${hazard.id}" value="${escapeHTML(parameterValue)}" ${isChecked ? "" : "disabled"} placeholder="Enter value">
          </div>`
        : "";
      item.innerHTML = `
        <div class="d-flex align-items-start gap-2">
          <input class="form-check-input flex-shrink-0 js-hazard-checkbox" type="checkbox" value="${hazard.id}" ${isChecked ? "checked" : ""}>
          <div>
            <div class="fw-semibold">${escapeHTML(hazard.name)}</div>
            <div class="small text-muted">${description}</div>
          </div>
        </div>
        ${parameterMarkup}
      `;
      const checkbox = item.querySelector(".js-hazard-checkbox");
      const paramInput = item.querySelector(".js-hazard-parameter");
      checkbox.addEventListener("change", (event) => {
        const id = parseInt(event.target.value, 10);
        if (event.target.checked) {
          const entry = state.hazardSelection.get(id) || { id, parameter_value: paramInput?.value ?? "" };
          state.hazardSelection.set(id, entry);
          if (paramInput) {
            paramInput.removeAttribute("disabled");
            paramInput.classList.remove('is-invalid');
            paramInput.focus();
          }
        } else {
          state.hazardSelection.delete(id);
          if (paramInput) {
            paramInput.value = "";
            paramInput.setAttribute("disabled", "disabled");
            paramInput.classList.remove('is-invalid');
          }
        }
        renderSelectedHazards();
      });
      if (paramInput) {
        paramInput.addEventListener("input", (event) => {
          const id = parseInt(event.target.dataset.hazardId, 10);
          const value = event.target.value;
          const entry = state.hazardSelection.get(id) || { id, parameter_value: value };
          entry.parameter_value = value;
          state.hazardSelection.set(id, entry);
          const checkboxEl = item.querySelector(".js-hazard-checkbox");
          if (!checkboxEl.checked) {
            checkboxEl.checked = true;
          }
          renderSelectedHazards();
        });
      }
      hazardOptionsEl.appendChild(item);
    });
  });
}

function openControlModal(taskId, phase = ControlPhase.EXISTING, hazardId = null) {
  state.activeTaskId = taskId;
  state.activeControlPhase = phase;
  state.activeHazardId = hazardId;
  
  let selected = [];
  if (hazardId) {
    // Hazard-specific controls
    const task = getTask(taskId);
    const hazard = task?.hazards?.find(h => h.id === hazardId);
    selected = hazard?.controls?.[phase] ?? [];
  } else {
    // Legacy task-level controls
    selected = getTask(taskId)?.controls?.[phase] ?? [];
  }
  
  state.controlSelection = new Set(selected.map((control) => control.id));
  controlSearchEl.value = "";
  controlModalTitleEl.textContent = phase === ControlPhase.EXISTING ? "Select Existing Controls" : "Select Additional Controls";
  controlPhaseLabelEl.textContent = phase === ControlPhase.EXISTING ? "Current" : "Planned";
  renderSelectedControls();
  renderControlOptions("");
  controlModal?.show();
}

async function handleHazardModalSave() {
  if (!state.activeTaskId) return;
  const selectedHazards = Array.from(state.hazardSelection.values());
  
  // Update parameter values from current input field values
  for (const entry of selectedHazards) {
    const hazardMeta = state.hazards.find((hazard) => hazard.id === entry.id);
    if (!hazardMeta) continue;
    
    // Get current parameter value from input field
    const input = hazardModalEl?.querySelector(`#hazard-parameter-${entry.id}`);
    const currentValue = input?.value?.trim() || "";
    entry.parameter_value = currentValue;
    state.hazardSelection.set(entry.id, entry);
    
    if (hazardMeta.requires_parameter && !currentValue) {
      flashMessage(`Enter ${hazardMeta.parameter_label || "a parameter"} for ${hazardMeta.name}.`, "warning");
      if (input) {
        input.removeAttribute('disabled');
        input.classList.add('is-invalid');
        input.focus();
      }
      return;
    }
    if (input) {
      input.classList.remove('is-invalid');
    }
  }
  try {
    const data = await fetchJSON(`/api/tasks/${state.activeTaskId}/hazards`, {
      method: "PUT",
      body: JSON.stringify({ hazards: Array.from(state.hazardSelection.values()) }),
    });
    mergeTask(data.task);
    renderTasks();
    hazardModal?.hide();
  } catch (error) {
    flashMessage(`Unable to update hazards: ${error.message}`, "danger");
  }
}

function getCategoryClass(category) {
  const categoryMap = {
    "Elimination": "category-elimination",
    "Substitution": "category-substitution", 
    "Engineering Controls": "category-engineering",
    "Administrative Controls": "category-administrative",
    "Personal Protective Equipment": "category-ppe"
  };
  return categoryMap[category] || "";
}

function renderSelectedControls() {
  if (!selectedControlsEl) return;
  
  if (state.controlSelection.size === 0) {
    selectedControlsEl.innerHTML = '<div class="text-muted small">No controls selected</div>';
    return;
  }
  
  const selectedControls = state.controls.filter(control => 
    state.controlSelection.has(control.id)
  );
  
  selectedControlsEl.innerHTML = `
    <div class="mb-2">
      <strong class="small text-muted">SELECTED CONTROLS (${selectedControls.length})</strong>
    </div>
    <div class="d-flex flex-wrap gap-1">
      ${selectedControls.map(control => {
        // Get parameter value from state
        const parameterValue = state.controlParameterValues.get(control.id) || '';
        const hasParameter = control.requires_parameter && control.parameter_label;
        
        let displayText = escapeHTML(control.name);
        if (hasParameter && parameterValue) {
          displayText += ` <small class="text-light">(${escapeHTML(parameterValue)})</small>`;
        }
        
        const title = hasParameter && parameterValue ? 
          `${control.name} - ${control.parameter_label}: ${parameterValue}` : 
          control.name;
        
        return `
          <span class="badge bg-primary d-flex align-items-center gap-1" title="${escapeHTML(title)}">
            ${displayText}
            <button type="button" class="btn-close btn-close-white" style="font-size: 0.6em;" 
                    onclick="removeSelectedControl(${control.id})" title="Remove control"></button>
          </span>
        `;
      }).join('')}
    </div>
  `;
}

function removeSelectedControl(controlId) {
  state.controlSelection.delete(controlId);
  state.controlParameterValues.delete(controlId); // Clean up parameter value
  renderSelectedControls();
  renderControlOptions(controlSearchEl?.value || "");
}

// Make function globally accessible for onclick handlers
window.removeSelectedControl = removeSelectedControl;

// Personnel Modal Functions
let personnelSelection = new Set();

function openPersonnelModal(taskId) {
  state.activeTaskId = taskId;
  const task = getTask(taskId);
  if (!task) return;
  
  // Parse current personnel selection
  personnelSelection.clear();
  if (task.personnel_at_risk) {
    const currentPersonnel = task.personnel_at_risk.split(',').map(p => p.trim()).filter(p => p);
    currentPersonnel.forEach(person => personnelSelection.add(person));
  }
  
  renderPersonnelOptions();
  renderSelectedPersonnel();
  personnelModal?.show();
}

function renderPersonnelOptions() {
  if (!personnelOptionsEl) return;
  
  personnelOptionsEl.innerHTML = '';
  
  state.personnel.forEach(person => {
    const isSelected = personnelSelection.has(person.name);
    const item = document.createElement("label");
    item.className = "list-group-item d-flex align-items-center gap-2";
    
    item.innerHTML = `
      <input class="form-check-input" type="checkbox" value="${escapeHTML(person.name)}" ${isSelected ? 'checked' : ''}>
      <div class="flex-grow-1">
        <div class="fw-semibold">${escapeHTML(person.name)}</div>
        ${person.description ? `<div class="small text-muted">${escapeHTML(person.description)}</div>` : ''}
      </div>
    `;
    
    const checkbox = item.querySelector('input[type="checkbox"]');
    checkbox.addEventListener('change', (event) => {
      const personName = event.target.value;
      if (event.target.checked) {
        personnelSelection.add(personName);
      } else {
        personnelSelection.delete(personName);
      }
      renderSelectedPersonnel();
    });
    
    personnelOptionsEl.appendChild(item);
  });
}

function renderSelectedPersonnel() {
  if (!selectedPersonnelEl) return;
  
  if (personnelSelection.size === 0) {
    selectedPersonnelEl.innerHTML = '<div class="text-muted small">No personnel selected</div>';
    return;
  }
  
  selectedPersonnelEl.innerHTML = `
    <div class="mb-2">
      <strong class="small text-muted">SELECTED PERSONNEL (${personnelSelection.size})</strong>
    </div>
    <div class="d-flex flex-wrap gap-1">
      ${Array.from(personnelSelection).map(person => `
        <span class="badge bg-info d-flex align-items-center gap-1">
          ${escapeHTML(person)}
          <button type="button" class="btn-close btn-close-white" style="font-size: 0.6em;" 
                  onclick="removeSelectedPersonnel('${escapeHTML(person)}')" title="Remove personnel"></button>
        </span>
      `).join('')}
    </div>
  `;
}

function removeSelectedPersonnel(personName) {
  personnelSelection.delete(personName);
  renderSelectedPersonnel();
  renderPersonnelOptions();
}

// Make function globally accessible
window.removeSelectedPersonnel = removeSelectedPersonnel;

async function handlePersonnelModalSave() {
  if (!state.activeTaskId) return;
  
  try {
    const personnelString = Array.from(personnelSelection).join(', ');
    
    const response = await fetch(`/api/tasks/${state.activeTaskId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        personnel_at_risk: personnelString
      })
    });
    
    if (response.ok) {
      const task = getTask(state.activeTaskId);
      if (task) {
        task.personnel_at_risk = personnelString;
        renderTasks();
      }
      personnelModal?.hide();
      flashMessage('Personnel updated successfully', 'success');
    } else {
      throw new Error('Failed to update personnel');
    }
  } catch (error) {
    console.error('Error updating personnel:', error);
    flashMessage('Failed to update personnel', 'danger');
  }
}

function renderControlOptions(filter = "") {
  if (!controlOptionsEl) return;
  const term = filter.toLowerCase();
  controlOptionsEl.innerHTML = "";
  
  // Filter controls based on search term
  const filteredControls = state.controls.filter((control) =>
    !term || control.name.toLowerCase().includes(term) || control.category.toLowerCase().includes(term)
  );
  
  // Group existing categories into hierarchy
  const categoryMapping = {
    // Match exact case from console log
    "Electrical Isolation": "Engineering Controls",
    "Handling Equipment": "Engineering Controls", 
    "Communication": "Administrative Controls",
    "Procedural": "Administrative Controls", 
    "Supervision": "Administrative Controls",
    "PPE": "Personal Protective Equipment",
    // Also keep uppercase versions for compatibility
    "ELECTRICAL ISOLATION": "Engineering Controls",
    "HANDLING EQUIPMENT": "Engineering Controls",
    "COMMUNICATION": "Administrative Controls",
    "PROCEDURAL": "Administrative Controls", 
    "SUPERVISION": "Administrative Controls",
    "Training": "Administrative Controls",
    "Procedures": "Administrative Controls",
    "Monitoring": "Administrative Controls"
  };
  
  // Remap controls to hierarchy categories
  const hierarchyControlsByCategory = {};
  filteredControls.forEach((control) => {
    const originalCategory = control.category || "Other";
    const hierarchyCategory = categoryMapping[originalCategory] || originalCategory;
    
    if (!hierarchyControlsByCategory[hierarchyCategory]) {
      hierarchyControlsByCategory[hierarchyCategory] = [];
    }
    hierarchyControlsByCategory[hierarchyCategory].push(control);
  });
  
  // Define category order (hierarchy of controls)
  const categoryOrder = [
    "Elimination",
    "Substitution", 
    "Engineering Controls",
    "Administrative Controls",
    "Personal Protective Equipment",
    "General",
    "Other"
  ];
  
  // Sort categories by hierarchy, then alphabetically for unlisted ones
  const sortedCategories = Object.keys(hierarchyControlsByCategory).sort((a, b) => {
    const aIndex = categoryOrder.indexOf(a);
    const bIndex = categoryOrder.indexOf(b);
    
    if (aIndex !== -1 && bIndex !== -1) {
      return aIndex - bIndex;
    } else if (aIndex !== -1) {
      return -1;
    } else if (bIndex !== -1) {
      return 1;
    } else {
      return a.localeCompare(b);
    }
  });
  
  // Debug: log what categories we have
  console.log("=== CONTROL CATEGORIZATION DEBUG ===");
  console.log("Total controls loaded:", state.controls.length);
  console.log("Filtered controls:", filteredControls.length);
  console.log("Original control categories:", [...new Set(filteredControls.map(c => c.category))]);
  console.log("Category mapping:", categoryMapping);
  console.log("Available hierarchy categories:", sortedCategories);
  console.log("Controls by hierarchy category:", Object.keys(hierarchyControlsByCategory).map(cat => `${cat}: ${hierarchyControlsByCategory[cat].length} controls`));
  console.log("=== END DEBUG ===");
  
  // If no controls are found, show empty hierarchy categories
  if (sortedCategories.length === 0) {
    const defaultCategories = [
      "Elimination",
      "Substitution", 
      "Engineering Controls",
      "Administrative Controls",
      "Personal Protective Equipment"
    ];
    
    defaultCategories.forEach((category, categoryIndex) => {
      if (categoryIndex > 0) {
        const separator = document.createElement("div");
        separator.className = "border-top my-2";
        controlOptionsEl.appendChild(separator);
      }
      
      const categoryHeader = document.createElement("div");
      const categoryClass = getCategoryClass(category);
      categoryHeader.className = `px-3 py-2 control-category-header ${categoryClass}`;
      
      const effectivenessMap = {
        "Elimination": "Most Effective",
        "Substitution": "Very Effective", 
        "Engineering Controls": "Moderately Effective",
        "Administrative Controls": "Less Effective",
        "Personal Protective Equipment": "Least Effective"
      };
      
      const effectiveness = effectivenessMap[category] || "";
      categoryHeader.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <span class="fw-bold">${category}</span>
          ${effectiveness ? `<small class="text-muted">${effectiveness}</small>` : ''}
        </div>
      `;
      controlOptionsEl.appendChild(categoryHeader);
      
      // Add empty state message
      const emptyMessage = document.createElement("div");
      emptyMessage.className = "px-3 py-2 text-muted small";
      emptyMessage.textContent = "No controls available in this category";
      controlOptionsEl.appendChild(emptyMessage);
    });
    return;
  }

  // Render controls grouped by category
  sortedCategories.forEach((category, categoryIndex) => {
    const controls = hierarchyControlsByCategory[category];
    
    // Add category header
    if (categoryIndex > 0) {
      const separator = document.createElement("div");
      separator.className = "border-top my-2";
      controlOptionsEl.appendChild(separator);
    }
    
    const categoryHeader = document.createElement("div");
    const categoryClass = getCategoryClass(category);
    categoryHeader.className = `px-3 py-2 control-category-header ${categoryClass}`;
    
    // Add effectiveness description
    const effectivenessMap = {
      "Elimination": "Most Effective",
      "Substitution": "Very Effective", 
      "Engineering Controls": "Moderately Effective",
      "Administrative Controls": "Less Effective",
      "Personal Protective Equipment": "Least Effective"
    };
    
    const effectiveness = effectivenessMap[category] || "";
    categoryHeader.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span class="fw-bold">${category}</span>
        ${effectiveness ? `<small class="text-muted">${effectiveness}</small>` : ''}
      </div>
    `;
    controlOptionsEl.appendChild(categoryHeader);
    
    // Add controls in this category
    controls.forEach((control) => {
      const item = document.createElement("div");
      const categoryClass = getCategoryClass(category);
      item.className = `list-group-item border-0 control-item ${categoryClass}`;
      
      const hasParameter = control.requires_parameter && control.parameter_label;
      const isSelected = state.controlSelection.has(control.id);
      const parameterDisplay = hasParameter ? `${control.parameter_label}${control.parameter_unit ? ' (' + control.parameter_unit + ')' : ''}` : '';
      
      
      item.innerHTML = `
        <div class="d-flex align-items-start gap-2">
          <input class="form-check-input flex-shrink-0" type="checkbox" value="${control.id}" ${
            isSelected ? "checked" : ""
          }>
          <div class="flex-grow-1">
            <div class="fw-semibold">${escapeHTML(control.name)}</div>
            ${control.description ? `<div class="small text-muted">${escapeHTML(control.description)}</div>` : ""}
            ${hasParameter ? `<div class="small text-info mt-1"><i class="bi bi-gear me-1"></i>Parameter: ${escapeHTML(parameterDisplay)}</div>` : ""}
            ${hasParameter ? `
              <div class="mt-2 parameter-input" style="display: ${isSelected ? 'block' : 'none'};">
                <input type="text" class="form-control form-control-sm" 
                       placeholder="Enter ${escapeHTML(control.parameter_label)}${control.parameter_unit ? ' (' + escapeHTML(control.parameter_unit) + ')' : ''}" 
                       data-control-id="${control.id}"
                       data-parameter-name="${escapeHTML(control.parameter_label)}"
                       title="Specify the ${escapeHTML(parameterDisplay)} for this control">
              </div>
            ` : ""}
          </div>
        </div>
      `;
      
      const checkbox = item.querySelector("input[type='checkbox']");
      const parameterInput = item.querySelector(".parameter-input");
      
      checkbox.addEventListener("change", (event) => {
        const id = parseInt(event.target.value, 10);
        if (event.target.checked) {
          state.controlSelection.add(id);
          if (parameterInput) {
            parameterInput.style.display = 'block';
          }
        } else {
          state.controlSelection.delete(id);
          state.controlParameterValues.delete(id); // Clear parameter value
          if (parameterInput) {
            parameterInput.style.display = 'none';
            const input = parameterInput.querySelector('input');
            if (input) input.value = '';
          }
        }
        renderSelectedControls();
      });
      
      // Add event listener for parameter input changes and restore existing values
      if (parameterInput) {
        const input = parameterInput.querySelector('input');
        if (input) {
          // Restore existing parameter value if it exists
          const existingValue = state.controlParameterValues.get(control.id);
          if (existingValue) {
            input.value = existingValue;
          }
          
          input.addEventListener('input', (event) => {
            const controlId = parseInt(input.dataset.controlId);
            const value = event.target.value.trim();
            if (value) {
              state.controlParameterValues.set(controlId, value);
            } else {
              state.controlParameterValues.delete(controlId);
            }
            renderSelectedControls();
          });
        }
      }
      
      controlOptionsEl.appendChild(item);
    });
  });
}

async function handleControlModalSave() {
  if (!state.activeTaskId || !state.activeControlPhase) return;
  try {
    let apiUrl;
    if (state.activeHazardId) {
      // Use hazard-specific endpoint
      apiUrl = `/api/tasks/${state.activeTaskId}/hazards/${state.activeHazardId}/controls`;
    } else {
      // Use legacy task-level endpoint
      apiUrl = `/api/tasks/${state.activeTaskId}/controls`;
    }
    
    // Collect parameter values for selected controls
    const controlsWithParameters = [];
    let hasValidationError = false;
    
    Array.from(state.controlSelection).forEach(controlId => {
      const parameterInput = document.querySelector(`input[data-control-id="${controlId}"]`);
      const control = { id: controlId };
      
      if (parameterInput) {
        const parameterName = parameterInput.dataset.parameterName;
        const parameterValue = parameterInput.value.trim();
        
        if (parameterValue) {
          control.parameter_value = `${parameterName}: ${parameterValue}`;
        } else {
          // Optional: You can make parameters required by uncommenting the lines below
          // parameterInput.classList.add('is-invalid');
          // hasValidationError = true;
          // flashMessage(`Please enter a value for ${parameterName}`, "warning");
        }
      }
      
      controlsWithParameters.push(control);
    });
    
    if (hasValidationError) {
      return;
    }
    
    const data = await fetchJSON(apiUrl, {
      method: "PUT",
      body: JSON.stringify({
        phase: state.activeControlPhase,
        control_ids: Array.from(state.controlSelection),
        controls_with_parameters: controlsWithParameters,
      }),
    });
    mergeTask(data.task);
    renderTasks();
    controlModal?.hide();
  } catch (error) {
    flashMessage(`Unable to update controls: ${error.message}`, "danger");
  }
}

function mergeTask(updatedTask) {
  const index = state.tasks.findIndex((task) => task.id === updatedTask.id);
  if (index >= 0) {
    state.tasks[index] = updatedTask;
  } else {
    state.tasks.push(updatedTask);
  }
}

function getTask(taskId) {
  return state.tasks.find((task) => task.id === taskId);
}

async function fetchJSON(url, options = {}) {
  const headers = options.headers ? new Headers(options.headers) : new Headers();
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(url, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
}

function flashMessage(message, level = "info") {
  if (!messageArea) return;
  const alert = document.createElement("div");
  alert.className = `alert alert-${level}`;
  alert.role = "alert";
  alert.textContent = message;
  messageArea.appendChild(alert);
  setTimeout(() => alert.remove(), 5000);
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"]/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  })[char]);
}

document.addEventListener("DOMContentLoaded", init);
