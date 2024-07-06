import "../globals.css";

export default function LandingLayout({ children }) {
  return (
    <div className="hero h-full">
      <div className="overlay w-full flex-grow">
        <div className="flex-grow">{children}</div>
      </div>
    </div>
  );
}
