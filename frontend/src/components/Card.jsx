import React from "react";

function Card({ title, text, custom }) {
  return (
    <div className="card mb-3 border-0 bg-light p-2" style={{ width: "18rem" }}>
      <div className="card-body">
        <h5 className="card-title">{title}</h5>
        <p className="card-text mb-3">{text}</p>
        {custom && <div className="px-2">{custom}</div>}
      </div>
    </div>
  );
}

export default Card;
