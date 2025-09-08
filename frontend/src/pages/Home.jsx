import React from "react";
import Layout from "../components/Layout";
import Card from "../components/Card";

function Home() {
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("Upload successful ✅");
      } else {
        alert("Upload failed ❌");
      }
    } catch (error) {
      console.error(error);
      alert("Error uploading file ❌");
    }
  };

  const cardsData = [
    { 
      title: "Snap & Store", 
      text: "Take a photo or screenshot of your receipts and let AI organize them automatically.", 
      custom: (
        <div className="row gap-2">
          <small 
            className="col bg-success text-white py-1 rounded text-center cursor-pointer"
            onClick={() => document.getElementById("fileInput").click()}
          >
            Try it !
          </small>
          <small className="col bg-white text-muted py-1 rounded text-center">
            See data
          </small>
        </div>
      )
    },
  ];

  return (
    <Layout>
      <h1 className="mb-5">Hi Igor 👋🏻</h1>
      <div className="d-flex flex-wrap gap-3">
        {cardsData.map((card, index) => (
          <Card key={index} title={card.title} text={card.text} custom={card.custom}/>
        ))}
      </div>

      {/* Hidden file input for camera / upload */}
      <input
        type="file"
        id="fileInput"
        accept="image/*"
        capture="environment"
        style={{ display: "none" }}
        onChange={handleFileUpload}
      />
    </Layout>
  );
}

export default Home;
