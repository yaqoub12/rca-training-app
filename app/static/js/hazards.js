// Hazards Catalog Management
let hazards = [];
let filteredHazards = [];
let editingHazard = null;

// DOM Elements
const hazardsTableBody = document.getElementById('hazardsTableBody');
const hazardSearch = document.getElementById('hazardSearch');
const categoryFilter = document.getElementById('categoryFilter');
const riskFilter = document.getElementById('riskFilter');
const addHazardBtn = document.getElementById('addHazardBtn');
const hazardModal = new bootstrap.Modal(document.getElementById('hazardModal'));
const hazardForm = document.getElementById('hazardForm');
const saveHazardBtn = document.getElementById('saveHazardBtn');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  await loadHazards();
  attachEventListeners();
});

async function loadHazards() {
  try {
    const response = await fetch('/api/catalog/hazards');
    const data = await response.json();
    hazards = data.hazards || [];
    filteredHazards = [...hazards];
    
    // Populate category filter
    const categories = [...new Set(hazards.map(h => h.category))].sort();
    categoryFilter.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(cat => {
      categoryFilter.innerHTML += `<option value="${cat}">${cat}</option>`;
    });
    
    renderHazards();
  } catch (error) {
    console.error('Failed to load hazards:', error);
    showAlert('Failed to load hazards', 'danger');
  }
}

function attachEventListeners() {
  hazardSearch.addEventListener('input', filterHazards);
  categoryFilter.addEventListener('change', filterHazards);
  riskFilter.addEventListener('change', filterHazards);
  addHazardBtn.addEventListener('click', () => openHazardModal());
  saveHazardBtn.addEventListener('click', saveHazard);
  
  // Parameter fields visibility toggle
  const requiresParameterCheckbox = document.getElementById('requiresParameter');
  requiresParameterCheckbox.addEventListener('change', toggleParameterFields);
  
  // Event delegation for edit and delete buttons
  hazardsTableBody.addEventListener('click', (event) => {
    const editBtn = event.target.closest('[data-action="edit"]');
    const deleteBtn = event.target.closest('[data-action="delete"]');
    
    if (editBtn) {
      const hazardId = parseInt(editBtn.dataset.hazardId);
      editHazard(hazardId);
    } else if (deleteBtn) {
      const hazardId = parseInt(deleteBtn.dataset.hazardId);
      deleteHazard(hazardId);
    }
  });
}

function toggleParameterFields() {
  const requiresParameter = document.getElementById('requiresParameter').checked;
  const parameterFields = document.getElementById('parameterFields');
  const parameterUnitField = document.getElementById('parameterUnitField');
  
  if (requiresParameter) {
    parameterFields.style.display = 'block';
    parameterUnitField.style.display = 'block';
  } else {
    parameterFields.style.display = 'none';
    parameterUnitField.style.display = 'none';
    document.getElementById('parameterLabel').value = '';
    document.getElementById('parameterUnit').value = '';
  }
}

function filterHazards() {
  const searchTerm = hazardSearch.value.toLowerCase();
  const selectedCategory = categoryFilter.value;
  const selectedRisk = riskFilter.value;
  
  filteredHazards = hazards.filter(hazard => {
    const matchesSearch = !searchTerm || 
      hazard.name.toLowerCase().includes(searchTerm) ||
      hazard.description.toLowerCase().includes(searchTerm);
    
    const matchesCategory = !selectedCategory || hazard.category === selectedCategory;
    
    let matchesRisk = true;
    if (selectedRisk) {
      const riskScore = hazard.default_likelihood * hazard.default_severity;
      const [min, max] = selectedRisk.split('-').map(Number);
      matchesRisk = riskScore >= min && riskScore <= max;
    }
    
    return matchesSearch && matchesCategory && matchesRisk;
  });
  
  renderHazards();
}

function renderHazards() {
  if (filteredHazards.length === 0) {
    hazardsTableBody.innerHTML = `
      <tr>
        <td colspan="7" class="text-center py-5 text-muted">
          <i class="bi bi-search fs-1 d-block mb-2"></i>
          No hazards found
        </td>
      </tr>
    `;
    return;
  }
  
  // Group hazards by category
  const hazardsByCategory = {};
  filteredHazards.forEach(hazard => {
    if (!hazardsByCategory[hazard.category]) {
      hazardsByCategory[hazard.category] = [];
    }
    hazardsByCategory[hazard.category].push(hazard);
  });
  
  // Sort categories
  const sortedCategories = Object.keys(hazardsByCategory).sort();
  
  let tableHTML = '';
  
  sortedCategories.forEach((category, categoryIndex) => {
    const hazards = hazardsByCategory[category];
    
    // Add category header row
    tableHTML += `
      <tr class="table-secondary">
        <td colspan="7" class="fw-bold py-2">
          <i class="bi bi-folder me-2"></i>
          ${escapeHtml(category)} 
          <span class="badge bg-primary ms-2">${hazards.length}</span>
        </td>
      </tr>
    `;
    
    // Add hazards in this category
    hazards.forEach(hazard => {
      const riskScore = hazard.default_likelihood * hazard.default_severity;
      const riskClass = getRiskClass(riskScore);
      const riskLabel = getRiskLabel(riskScore);
      
      tableHTML += `
        <tr data-hazard-id="${hazard.id}">
          <td class="text-center">
            <i class="bi bi-exclamation-triangle text-warning"></i>
          </td>
          <td>
            <div class="fw-semibold">${escapeHtml(hazard.name)}</div>
          </td>
          <td>
            <span class="badge bg-secondary">${escapeHtml(hazard.category)}</span>
          </td>
          <td>
            <div class="text-truncate" style="max-width: 300px;" title="${escapeHtml(hazard.description)}">
              ${escapeHtml(hazard.description)}
            </div>
          </td>
          <td class="text-center">
            <span class="badge ${riskClass}">${riskLabel}</span>
            <div class="small text-muted">L:${hazard.default_likelihood} × S:${hazard.default_severity}</div>
          </td>
          <td class="text-center">
            ${hazard.requires_parameter ? 
              `<i class="bi bi-check-circle text-success" title="Requires: ${hazard.parameter_label || 'Parameter'} ${hazard.parameter_unit ? '(' + hazard.parameter_unit + ')' : ''}"></i>` : 
              `<i class="bi bi-dash-circle text-muted" title="No parameter"></i>`
            }
            ${hazard.requires_parameter && hazard.parameter_label ? 
              `<div class="small text-muted">${hazard.parameter_label}</div>` : ''
            }
          </td>
          <td>
            <div class="btn-group btn-group-sm">
              <button class="btn btn-outline-primary" data-action="edit" data-hazard-id="${hazard.id}" title="Edit">
                <i class="bi bi-pencil"></i>
              </button>
              <button class="btn btn-outline-danger" data-action="delete" data-hazard-id="${hazard.id}" title="Delete">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    });
  });
  
  hazardsTableBody.innerHTML = tableHTML;
}

function getRiskClass(score) {
  if (score <= 5) return 'bg-success';
  if (score <= 10) return 'bg-warning';
  if (score <= 15) return 'bg-orange';
  return 'bg-danger';
}

function getRiskLabel(score) {
  if (score <= 5) return 'LOW';
  if (score <= 10) return 'MEDIUM';
  if (score <= 15) return 'HIGH';
  return 'CRITICAL';
}

function openHazardModal(hazard = null) {
  editingHazard = hazard;
  const modalTitle = document.getElementById('hazardModalTitle');
  
  if (hazard) {
    modalTitle.textContent = 'Edit Hazard';
    document.getElementById('hazardId').value = hazard.id;
    document.getElementById('hazardName').value = hazard.name;
    document.getElementById('hazardCategory').value = hazard.category;
    document.getElementById('hazardDescription').value = hazard.description;
    document.getElementById('defaultLikelihood').value = hazard.default_likelihood;
    document.getElementById('defaultSeverity').value = hazard.default_severity;
    document.getElementById('requiresParameter').checked = hazard.requires_parameter;
    document.getElementById('parameterLabel').value = hazard.parameter_label || '';
    document.getElementById('parameterUnit').value = hazard.parameter_unit || '';
  } else {
    modalTitle.textContent = 'Add New Hazard';
    hazardForm.reset();
    document.getElementById('hazardId').value = '';
    document.getElementById('parameterLabel').value = '';
    document.getElementById('parameterUnit').value = '';
  }
  
  // Toggle parameter fields visibility
  toggleParameterFields();
  
  hazardModal.show();
}

function editHazard(hazardId) {
  const hazard = hazards.find(h => h.id === hazardId);
  if (hazard) {
    openHazardModal(hazard);
  }
}


async function saveHazard() {
  const formData = new FormData(hazardForm);
  const hazardData = {
    name: document.getElementById('hazardName').value,
    category: document.getElementById('hazardCategory').value,
    description: document.getElementById('hazardDescription').value,
    default_likelihood: parseInt(document.getElementById('defaultLikelihood').value),
    default_severity: parseInt(document.getElementById('defaultSeverity').value),
    requires_parameter: document.getElementById('requiresParameter').checked,
    parameter_label: document.getElementById('parameterLabel').value,
    parameter_unit: document.getElementById('parameterUnit').value
  };
  
  if (!hazardData.name || !hazardData.category) {
    showAlert('Please fill in all required fields', 'warning');
    return;
  }
  
  try {
    const hazardId = document.getElementById('hazardId').value;
    const isEdit = hazardId !== '';
    
    const response = await fetch(
      isEdit ? `/api/catalog/hazards/${hazardId}` : '/api/catalog/hazards',
      {
        method: isEdit ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(hazardData)
      }
    );
    
    if (response.ok) {
      const result = await response.json();
      showAlert(`Hazard ${isEdit ? 'updated' : 'created'} successfully`, 'success');
      hazardModal.hide();
      await loadHazards();
    } else {
      throw new Error('Failed to save hazard');
    }
  } catch (error) {
    console.error('Error saving hazard:', error);
    showAlert('Failed to save hazard', 'danger');
  }
}

async function deleteHazard(hazardId) {
  const hazard = hazards.find(h => h.id === hazardId);
  if (!hazard) return;
  
  if (!confirm(`Are you sure you want to delete "${hazard.name}"?`)) {
    return;
  }
  
  try {
    const response = await fetch(`/api/catalog/hazards/${hazardId}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      showAlert('Hazard deleted successfully', 'success');
      await loadHazards();
    } else {
      throw new Error('Failed to delete hazard');
    }
  } catch (error) {
    console.error('Error deleting hazard:', error);
    showAlert('Failed to delete hazard', 'danger');
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
