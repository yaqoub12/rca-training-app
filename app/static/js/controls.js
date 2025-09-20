// Controls Catalog Management
let controls = [];
let filteredControls = [];
let editingControl = null;

// DOM Elements
const controlsTableBody = document.getElementById('controlsTableBody');
const controlSearch = document.getElementById('controlSearch');
const categoryFilter = document.getElementById('categoryFilter');
const effectivenessFilter = document.getElementById('effectivenessFilter');
const addControlBtn = document.getElementById('addControlBtn');
const controlModal = new bootstrap.Modal(document.getElementById('controlModal'));
const controlForm = document.getElementById('controlForm');
const saveControlBtn = document.getElementById('saveControlBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadControls();
  attachEventListeners();
});

async function loadControls() {
  try {
    const response = await fetch('/api/catalog/controls');
    const data = await response.json();
    controls = data.controls || [];
    filteredControls = [...controls];
    renderControls();
  } catch (error) {
    console.error('Failed to load controls:', error);
    showAlert('Failed to load controls', 'danger');
  }
}

function attachEventListeners() {
  controlSearch.addEventListener('input', filterControls);
  categoryFilter.addEventListener('change', filterControls);
  effectivenessFilter.addEventListener('change', filterControls);
  
  // Event delegation for edit and delete buttons
  controlsTableBody.addEventListener('click', (event) => {
    const editBtn = event.target.closest('[data-action="edit"]');
    const deleteBtn = event.target.closest('[data-action="delete"]');
    
    if (editBtn) {
      const controlId = parseInt(editBtn.dataset.controlId);
      editControl(controlId);
    } else if (deleteBtn) {
      const controlId = parseInt(deleteBtn.dataset.controlId);
      deleteControl(controlId);
    }
  });
}

function filterControls() {
  const searchTerm = controlSearch.value.toLowerCase();
  const selectedCategory = categoryFilter.value;
  const selectedEffectiveness = effectivenessFilter.value;
  
  filteredControls = controls.filter(control => {
    const matchesSearch = !searchTerm || 
      control.name.toLowerCase().includes(searchTerm) ||
      control.description.toLowerCase().includes(searchTerm);
    
    const matchesCategory = !selectedCategory || control.category === selectedCategory;
    const matchesEffectiveness = !selectedEffectiveness || control.effectiveness.toString() === selectedEffectiveness;
    
    return matchesSearch && matchesCategory && matchesEffectiveness;
  });
  
  renderControls();
}

function renderControls() {
  if (filteredControls.length === 0) {
    controlsTableBody.innerHTML = `
      <tr>
        <td colspan="8" class="text-center py-4 text-muted">
          No controls found
        </td>
      </tr>
    `;
    return;
  }
  
  controlsTableBody.innerHTML = filteredControls.map(control => {
    const categoryClass = getCategoryClass(control.category);
    const effectivenessClass = getEffectivenessClass(control.effectiveness);
    
    return `
      <tr data-control-id="${control.id}">
        <td class="text-center">
          <i class="bi bi-shield-shaded ${categoryClass}"></i>
        </td>
        <td>
          <div class="fw-semibold">${escapeHtml(control.name)}</div>
        </td>
        <td>
          <span class="badge ${categoryClass}">${escapeHtml(control.category)}</span>
        </td>
        <td>
          <div class="text-truncate" style="max-width: 300px;" title="${escapeHtml(control.description)}">
            ${escapeHtml(control.description)}
          </div>
        </td>
        <td class="text-center">
          <span class="badge ${effectivenessClass}">${control.effectiveness}/5</span>
          <div class="small text-muted">${getEffectivenessLabel(control.effectiveness)}</div>
        </td>
        <td>
          ${control.requires_parameter ? `
            <div class="text-truncate" style="max-width: 140px;" title="${escapeHtml((control.parameter_label || '') + (control.parameter_unit ? ' (' + control.parameter_unit + ')' : ''))}">
              <i class="bi bi-gear text-info me-1"></i>
              <span class="small">${escapeHtml(control.parameter_label || 'Parameter')}</span>
              ${control.parameter_unit ? `<span class="text-muted small"> (${escapeHtml(control.parameter_unit)})</span>` : ''}
            </div>
          ` : '<span class="text-muted small">No parameter</span>'}
        </td>
        <td>
          <div class="text-truncate" style="max-width: 120px;" title="${escapeHtml(control.reference || '')}">
            ${control.reference ? escapeHtml(control.reference) : '<span class="text-muted small">No reference</span>'}
          </div>
        </td>
        <td>
          <div class="btn-group btn-group-sm">
            <button class="btn btn-outline-primary" data-action="edit" data-control-id="${control.id}" title="Edit">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-outline-danger" data-action="delete" data-control-id="${control.id}" title="Delete">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function getCategoryClass(category) {
  const categoryMap = {
    'Elimination': 'text-danger',
    'Substitution': 'text-warning',
    'Engineering Controls': 'text-info',
    'Administrative Controls': 'text-success',
    'Personal Protective Equipment': 'text-primary',
    'PPE': 'text-primary',
    'Communication': 'text-success',
    'Electrical Isolation': 'text-info',
    'Handling Equipment': 'text-info',
    'Procedural': 'text-success',
    'Supervision': 'text-success'
  };
  return categoryMap[category] || 'text-secondary';
}

function getEffectivenessClass(effectiveness) {
  if (effectiveness >= 4) return 'bg-success';
  if (effectiveness >= 3) return 'bg-info';
  if (effectiveness >= 2) return 'bg-warning';
  return 'bg-danger';
}

function getEffectivenessLabel(effectiveness) {
  const labels = {
    1: 'Low',
    2: 'Medium',
    3: 'High',
    4: 'Very High',
    5: 'Maximum'
  };
  return labels[effectiveness] || 'Unknown';
}

function openControlModal(control = null) {
  editingControl = control;
  const modalTitle = document.getElementById('controlModalTitle');
  
  if (control) {
    modalTitle.textContent = 'Edit Control';
    document.getElementById('controlId').value = control.id;
    document.getElementById('controlName').value = control.name;
    document.getElementById('controlCategory').value = control.category;
    document.getElementById('controlDescription').value = control.description;
    document.getElementById('effectiveness').value = control.effectiveness;
    document.getElementById('requiresParameter').checked = control.requires_parameter || false;
    document.getElementById('parameterLabel').value = control.parameter_label || '';
    document.getElementById('parameterUnit').value = control.parameter_unit || '';
    document.getElementById('controlReference').value = control.reference || '';
    toggleParameterFields();
  } else {
    modalTitle.textContent = 'Add New Control';
    controlForm.reset();
    document.getElementById('controlId').value = '';
    document.getElementById('requiresParameter').checked = false;
    toggleParameterFields();
  }
  
  controlModal.show();
}

function editControl(controlId) {
  const control = controls.find(c => c.id === controlId);
  if (control) {
    openControlModal(control);
  }
}


async function saveControl() {
  const controlData = {
    name: document.getElementById('controlName').value,
    category: document.getElementById('controlCategory').value,
    description: document.getElementById('controlDescription').value,
    effectiveness: parseInt(document.getElementById('effectiveness').value),
    requires_parameter: document.getElementById('requiresParameter').checked,
    parameter_label: document.getElementById('parameterLabel').value,
    parameter_unit: document.getElementById('parameterUnit').value,
    reference: document.getElementById('controlReference').value
  };
  
  if (!controlData.name || !controlData.category) {
    showAlert('Please fill in all required fields', 'warning');
    return;
  }
  
  try {
    const controlId = document.getElementById('controlId').value;
    const isEdit = controlId !== '';
    
    const response = await fetch(
      isEdit ? `/api/catalog/controls/${controlId}` : '/api/catalog/controls',
      {
        method: isEdit ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(controlData)
      }
    );
    
    if (response.ok) {
      const result = await response.json();
      showAlert(`Control ${isEdit ? 'updated' : 'created'} successfully`, 'success');
      controlModal.hide();
      await loadControls();
    } else {
      throw new Error('Failed to save control');
    }
  } catch (error) {
    console.error('Error saving control:', error);
    showAlert('Failed to save control', 'danger');
  }
}

async function deleteControl(controlId) {
  const control = controls.find(c => c.id === controlId);
  if (!control) return;
  
  if (!confirm(`Are you sure you want to delete "${control.name}"?`)) {
    return;
  }
  
  try {
    const response = await fetch(`/api/catalog/controls/${controlId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showAlert('Control deleted successfully', 'success');
      await loadControls();
    } else {
      throw new Error('Failed to delete control');
    }
  } catch (error) {
    console.error('Error deleting control:', error);
    showAlert('Failed to delete control', 'danger');
  }
}

function showAlert(message, type = 'info') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(alertDiv);
  
  setTimeout(() => {
    if (alertDiv.parentNode) {
      alertDiv.remove();
    }
  }, 5000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function toggleParameterFields() {
  const requiresParameter = document.getElementById('requiresParameter').checked;
  const parameterLabelGroup = document.getElementById('parameterLabelGroup');
  const parameterUnitGroup = document.getElementById('parameterUnitGroup');
  
  if (requiresParameter) {
    parameterLabelGroup.style.display = 'block';
    parameterUnitGroup.style.display = 'block';
  } else {
    parameterLabelGroup.style.display = 'none';
    parameterUnitGroup.style.display = 'none';
    // Clear the fields when hiding
    document.getElementById('parameterLabel').value = '';
    document.getElementById('parameterUnit').value = '';
  }
}

// Add event listeners
document.addEventListener('DOMContentLoaded', function() {
  loadControls();
  
  // Add control button
  document.getElementById('addControlBtn').addEventListener('click', function() {
    openControlModal();
  });
  
  // Save control button
  document.getElementById('saveControlBtn').addEventListener('click', function() {
    saveControl();
  });
  
  // Parameter checkbox toggle
  document.getElementById('requiresParameter').addEventListener('change', function() {
    toggleParameterFields();
  });
});
