(function() {
    'use strict';
    
    // Wait for DOM to load
    document.addEventListener('DOMContentLoaded', function() {
        const changelist = document.querySelector('#changelist');
        const filterSidebar = document.querySelector('#changelist-filter');
        
        if (!changelist || !filterSidebar) return;
        
        // Toggle filter sidebar on button click
        changelist.addEventListener('click', function(e) {
            // Check if clicked on the ::before pseudo element area
            const rect = changelist.getBoundingClientRect();
            const isToggleButton = (
                e.clientX >= rect.right - 120 && 
                e.clientY >= 120 && 
                e.clientY <= 160
            );
            
            if (isToggleButton) {
                filterSidebar.classList.toggle('show');
            }
        });
        
        // Close filter when clicking outside
        document.addEventListener('click', function(e) {
            if (!filterSidebar.contains(e.target) && 
                !changelist.contains(e.target) && 
                filterSidebar.classList.contains('show')) {
                filterSidebar.classList.remove('show');
            }
        });
        
        // Close on ESC key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && filterSidebar.classList.contains('show')) {
                filterSidebar.classList.remove('show');
            }
        });
    });
})();
