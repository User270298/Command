// Utility functions
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Enable dynamic searching
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keyup', function(e) {
            const searchText = e.target.value.toLowerCase();
            const items = document.querySelectorAll('.searchable-item');
            
            items.forEach(function(item) {
                const text = item.textContent.toLowerCase();
                if (text.includes(searchText)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
    
    // Record value validation
    const valueInput = document.getElementById('value');
    if (valueInput) {
        valueInput.addEventListener('input', function(e) {
            const value = e.target.value;
            // Remove all non-digit characters except for dot and comma
            e.target.value = value.replace(/[^\d.,]/g, '');
            // Replace comma with dot
            e.target.value = e.target.value.replace(/,/g, '.');
            // Only allow one dot
            const parts = e.target.value.split('.');
            if (parts.length > 2) {
                e.target.value = parts[0] + '.' + parts.slice(1).join('');
            }
        });
    }
    
    // Trip member selection
    const memberSelect = document.getElementById('members');
    if (memberSelect) {
        // Configure the member select as a multiple select with search
        $(memberSelect).select2({
            placeholder: 'Выберите участников...',
            allowClear: true,
            multiple: true,
            width: '100%'
        });
    }
    
    // Charts for statistics
    const chartCanvas = document.getElementById('statisticsChart');
    if (chartCanvas) {
        const ctx = chartCanvas.getContext('2d');
        
        // Get data from the data attributes
        const labels = JSON.parse(chartCanvas.dataset.labels || '[]');
        const values = JSON.parse(chartCanvas.dataset.values || '[]');
        const colors = generateColors(labels.length);
        
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
});

// Generate random colors for chart
function generateColors(count) {
    const colors = [];
    for (let i = 0; i < count; i++) {
        const hue = (i * 137) % 360;  // Use golden angle approximation
        colors.push(`hsl(${hue}, 70%, 60%)`);
    }
    return colors;
} 