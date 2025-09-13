import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

function SideMenu() {
  const [isVisible, setIsVisible] = useState(true);
  const location = useLocation();
  
  const toggleSidebar = () => {
    setIsVisible(!isVisible);
  };

  const navItems = [
    { path: "/", title: "AI Agents" },
    { path: "/dashboard", title: "Numbers" },
    { path: "/contact", title: "Contact" }
  ];

  return (
    <div
      className="d-flex flex-column justify-content-between bg-light vh-100 pt-3 border-end"
      style={{
        width: isVisible ? '280px' : '60px',
        transition: 'width 0.3s ease-in-out',
        position: 'relative'
      }}
    >
      {/* Toggle button area */}
      <div className="px-3 mb-4">
        {isVisible ? (
          <div className="d-flex justify-content-between align-items-center">
            <h6 className="text-dark mb-0 fw-bold">Navigation</h6>
            <button
              className="btn btn-dark btn-sm px-3 py-2 fw-semibold"
              onClick={toggleSidebar}
              title="Hide Navigation"
            >
              Hide
            </button>
          </div>
        ) : (
          <div className="d-flex justify-content-center">
            <button
              className="btn btn-dark btn-sm fw-semibold"
              onClick={toggleSidebar}
              title="Show Navigation"
              style={{
                writingMode: 'vertical-lr',
                textOrientation: 'mixed',
                minHeight: '80px',
                width: '36px'
              }}
            >
              Show
            </button>
          </div>
        )}
        {isVisible && <hr className="mt-3 mb-0" />}
      </div>

      {/* Navigation items - only show when expanded */}
      {isVisible && (
        <div className="flex-grow-1 px-3">
          <ul className="nav flex-column">
            {navItems.map((item) => (
              <li key={item.path} className="nav-item mb-2">
                <NavLink
                  to={item.path}
                  className={({ isActive }) => 
                    `nav-link rounded px-3 py-3 fw-semibold text-decoration-none d-block ${
                      isActive 
                        ? "bg-dark text-white" 
                        : "text-dark bg-transparent"
                    }`
                  }
                  style={{ transition: 'all 0.2s ease' }}
                  onMouseEnter={(e) => {
                    if (!e.target.classList.contains('text-white')) {
                      e.target.classList.add('bg-secondary', 'bg-opacity-25');
                      e.target.style.transform = 'translateX(4px)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!e.target.classList.contains('text-white')) {
                      e.target.classList.remove('bg-secondary', 'bg-opacity-25');
                      e.target.style.transform = 'translateX(0)';
                    }
                  }}
                >
                  {item.title}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Footer - only show when expanded */}
      {isVisible && (
        <div className="p-3 border-top bg-white">
          <a
            className="text-dark text-decoration-none d-block p-3 rounded fw-semibold text-center"
            href="/logout"
            title="Sign out"
            style={{ transition: 'all 0.2s ease' }}
            onMouseEnter={(e) => {
              e.target.classList.add('bg-danger', 'text-white');
            }}
            onMouseLeave={(e) => {
              e.target.classList.remove('bg-danger', 'text-white');
            }}
          >
            Sign out
          </a>
        </div>
      )}
    </div>
  );
}

export default SideMenu;