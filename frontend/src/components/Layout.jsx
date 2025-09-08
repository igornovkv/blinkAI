import React from "react";
import SideMenu from "./SideMenu";

function Layout({ children }) {
  return (
    <div className="d-flex">
      <SideMenu />
      <div className="flex-grow-1 p-5">
        {children}
      </div>
    </div>
  );
}

export default Layout;
