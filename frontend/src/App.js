import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import Layout from "@/components/Layout";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import Discover from "@/pages/Discover";
import MyListings from "@/pages/MyListings";
import NewListing from "@/pages/NewListing";
import ListingDetail from "@/pages/ListingDetail";
import Requests from "@/pages/Requests";
import Rewards from "@/pages/Rewards";
import Impact from "@/pages/Impact";
import Admin from "@/pages/Admin";
import Profile from "@/pages/Profile";
import { Toaster } from "sonner";

function Protected({ children, roles }) {
  const { user } = useAuth();
  if (user === null) {
    return (
      <div className="min-h-screen flex items-center justify-center text-[#695A62]">
        Loading…
      </div>
    );
  }
  if (user === false) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return children;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: "#FDFBF7",
                color: "#2A1B24",
                border: "1px solid rgba(42,27,36,0.1)",
                borderRadius: "16px",
              },
            }}
          />
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            <Route
              element={
                <Protected>
                  <Layout />
                </Protected>
              }
            >
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/discover" element={<Discover />} />
              <Route path="/listings" element={<MyListings />} />
              <Route path="/listings/new" element={<NewListing />} />
              <Route path="/listings/:id" element={<ListingDetail />} />
              <Route path="/requests" element={<Requests />} />
              <Route path="/rewards" element={<Rewards />} />
              <Route path="/impact" element={<Impact />} />
              <Route path="/profile" element={<Profile />} />
              <Route
                path="/admin"
                element={
                  <Protected roles={["admin"]}>
                    <Admin />
                  </Protected>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
