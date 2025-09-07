import React from "react";
import { NavLink, useLocation } from "react-router-dom";

function SideMenu() {
  return (
    <div className="d-flex flex-column bg-light vh-100 p-3 pt-5" style={{ width:'300px'}}>
        <ul className="nav nav-pills flex-column mt-3">
            <li className={"nav-item mb-2 rounded " + (location.pathname === "/" ? "bg-dark" : "")} >
                <NavLink to="/" className={({ isActive }) => isActive ? "nav-link text-white" : "nav-link text-muted"}>Home</NavLink>
            </li>
            <li className={"nav-item mb-2 rounded " + (location.pathname === "/dashboard" ? "bg-dark" : "")} >
                <NavLink to="/dashboard" className={({ isActive }) => isActive ? "nav-link text-white" : "nav-link text-muted"}>Dashboard</NavLink>
            </li>
            <li className={"nav-item mb-2 rounded " + (location.pathname === "/contact" ? "bg-dark" : "")} >
                <NavLink to="/contact" className={({ isActive }) => isActive ? "nav-link text-white" : "nav-link text-muted"}>Contact</NavLink>
            </li>
        </ul>
    </div>
  );
}

export default SideMenu;
