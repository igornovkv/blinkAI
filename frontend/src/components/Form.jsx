import { useState } from "react";
import api from "../api";
import { useNavigate, Link } from "react-router-dom";
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import newLogo from "../assets/logo/new_logo.png";

function Form({ route, method }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const navigate = useNavigate();
    
    const name = method === "login" ? "Log In" : "Register";
    
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        
        try {
            const res = await api.post(route, { username, password });
            if (method === "login") {
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                navigate("/");
            } else {
                navigate("/login");
            }
        } catch (error) {
            setError(error.response?.data?.detail || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };
    return (
        <div className="container-fluid d-flex align-items-center justify-content-center min-vh-100 py-4">
            <div className="row w-100 justify-content-center">
                <div className="col-12 col-sm-8 col-md-6 col-lg-4">
                    <div className="auth-container">
                        {/* Logo Container */}
                        <div className="logo-container text-center mb-4">
                            <img 
                                src={newLogo} 
                                alt="App logo" 
                                className="img-fluid mx-auto d-block" 
                                style={{
                                    height: 'clamp(200px, 25vh, 300px)', // Responsive height
                                    maxWidth: '280px',
                                    width: 'auto',
                                    objectFit: 'contain',
                                    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
                                }}
                            />
                        </div>
                        
                        {/* Form Card */}
                        <div className="card shadow-sm">
                            <div className="card-body p-4 p-md-5">
                                <div className="text-center mb-4">
                                    <h1 className="h3 mb-3">{name}</h1>
                                </div>
                                
                                <form onSubmit={handleSubmit}>
                                    {error && (
                                        <div className="alert alert-danger" role="alert" id="error-message">
                                            {error}
                                        </div>
                                    )}
                                    
                                    <div className="form-floating mb-3">
                                        <input
                                            type="text"
                                            id="username"
                                            className={`form-control ${error ? 'is-invalid' : ''}`}
                                            placeholder="Username"
                                            value={username}
                                            onChange={(e) => setUsername(e.target.value)}
                                            disabled={loading}
                                            required
                                            autoComplete={method === "login" ? "username" : "new-username"}
                                            aria-describedby={error ? "error-message" : undefined}
                                        />
                                        <label htmlFor="username">Username</label>
                                    </div>
                                    
                                    <div className="form-floating mb-4">
                                        <input
                                            type="password"
                                            id="password"
                                            className={`form-control ${error ? 'is-invalid' : ''}`}
                                            placeholder="Password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            disabled={loading}
                                            required
                                            autoComplete={method === "login" ? "current-password" : "new-password"}
                                            minLength={method === "register" ? 8 : undefined}
                                            aria-describedby={error ? "error-message" : undefined}
                                        />
                                        <label htmlFor="password">Password</label>
                                    </div>
                                    
                                    <button 
                                        className="btn btn-dark w-100 py-2 mb-3" 
                                        type="submit"
                                        disabled={loading || !username || !password}
                                    >
                                        {loading ? (
                                            <>
                                                <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                                                {method === "login" ? "Signing in..." : "Creating account..."}
                                            </>
                                        ) : (
                                            name
                                        )}
                                    </button>
                                </form>
                                
                                <hr className="my-4" />
                                
                                <div className="text-center">
                                    {method === "login" ? (
                                        <p className="mb-0">
                                            Don't have an account?{" "}
                                            <Link to="/register" className="text-dark text-decoration-underline fw-medium">
                                                Sign up
                                            </Link>
                                        </p>
                                    ) : (
                                        <p className="mb-0">
                                            Already have an account?{" "}
                                            <Link to="/login" className="text-dark text-decoration-underline fw-medium">
                                                Sign in
                                            </Link>
                                        </p>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Form;