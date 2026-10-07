import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import { ChatResultsProvider } from "./chatResults";
import ChatPanel from "./components/ChatPanel";
import ChatResultsStrip from "./components/ChatResultsStrip";
import Marquee from "./components/Marquee";
import Footer from "./components/Footer";
import NavBar from "./components/NavBar";
import About from "./pages/About";
import CreateAccount from "./pages/CreateAccount";
import Home from "./pages/Home";
import Login from "./pages/Login";
import ProductDetail from "./pages/ProductDetail";
import Products from "./pages/Products";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ChatResultsProvider>
          <NavBar />
          <Marquee />
          {/* Chat matches land here, above the page, on whatever route is open. */}
          <ChatResultsStrip />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:productId" element={<ProductDetail />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<Login />} />
              <Route path="/create-account" element={<CreateAccount />} />
            </Routes>
          </main>
          <Footer />
          {/* Floating panel, present on every page. */}
          <ChatPanel />
        </ChatResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
