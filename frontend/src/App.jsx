import React from "react"
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import Home from "./pages/Home"
import Dashboard from "./pages/Dashboard"
import Contact from "./pages/Contact"

function App() {
  return (
    <BrowserRouter>
      <Routes>
          <Route path = "/" element = {<Home/>}/>
          <Route path = "/dashboard" element = {<Dashboard/>}/>
          <Route path = "/contact" element = {<Contact/>}/>
      </Routes>
    </BrowserRouter>
  )
}

export default App
