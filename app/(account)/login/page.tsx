"use client";

import Link from "next/link";
import { HomeIcon, EyeIcon, EyeSlashIcon } from "@heroicons/react/16/solid";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { CompanyInstance, UserInstance } from "../../../util/wrapper/instance";
import { Company, User } from "../../../util/wrapper/static";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisible, setPasswordVisible] = useState(false);
  const [bMessage, setBMessage] = useState("Sign In");
  const router = useRouter();
  let user: CompanyInstance | UserInstance | null = null;

  let handleLogin = async (e) => {
    e.preventDefault();
    let requestCount = 0;
    setBMessage("Loading...");
    let [a, b] = await Promise.all([
      Company.login(email, password),
      User.login(email, password),
    ]);
    user = a ?? b;
    setBMessage("Sign In");
    if (!user) {
      alert("Invalid username or password.");
      ++requestCount;
      return;
    }

    if (user.verified) {
      router.push("/home");
    } else {
      if (user instanceof UserInstance) await User.verify(user.id, user.email);
      else await Company.verify(user.id, user.email);
      alert(
        "Email not verified. Please check your inbox for the verification email."
      );
    }

    if (requestCount > 10) {
      alert(
        "Too many attempts, account has been temporarily disabled. Please reset your password."
      );
    }
  };

  const handlePasswordReset = async () => {
    if (!email) {
      alert("Please enter your email address to reset your password.");
      return;
    }
    try {
      let finished = false;
      setTimeout(() => {
        if (!finished) alert("Request taking too long");
      }, 2000);
      (await User.resetPassword(email)) || (await Company.resetPassword(email));
      finished = true;
      alert("Password reset email sent! Check your inbox.");
    } catch (error) {
      alert(error.message);
    }
  };

  const togglePasswordVisibility = () => setPasswordVisible(!passwordVisible);

  return (
    <div>
      <button className="absolute ml-5 mt-5">
        <Link href="/">
          <HomeIcon className="md:size-12 size-10 fill-logo-purple/85"></HomeIcon>
        </Link>
      </button>
      <div className="font-poppins flex h-screen flex-col px-6 justify-center lg:px-8 bg-gradient-to-bl from-logo-purple/95 via-mid-purple/40 via-70% to-transparent">
        <div className="sm:mx-auto sm:w-full sm:max-w-sm">
          <img className="mx-auto h-14 w-auto" src="/logo.png" alt="Kinetik" />
          <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-off-white/90">
            Log in to your account
          </h2>
        </div>
        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-sm">
          <form className="space-y-3" onSubmit={handleLogin}>
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-semibold leading-6 text-off-white"
              >
                Email address
              </label>
              <div className="mt-2">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="block w-full rounded-md border-0 py-1.5 bg-off-white/40 text-gray-900 shadow-sm placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-logo-purple/75 sm:text-sm sm:leading-6"
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-sm font-semibold leading-6 text-off-white"
                >
                  Password
                </label>
                <div className="text-sm">
                  <button
                    type="button"
                    onClick={handlePasswordReset}
                    className="font-medium text-logo-purple hover:text-logo-purple/75"
                  >
                    Forgot password?
                  </button>
                </div>
              </div>
              <div className="mt-2 relative">
                <input
                  id="password"
                  name="password"
                  type={passwordVisible ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="block w-full rounded-md border-0 py-1.5 bg-off-white/40 text-gray-900 shadow-sm placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-logo-purple/75 sm:text-sm sm:leading-6"
                />
                <span
                  className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer"
                  onClick={togglePasswordVisibility}
                >
                  {passwordVisible ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-600" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-600" />
                  )}
                </span>
              </div>
            </div>
            <div>
              <button
                type="submit"
                className="flex w-full justify-center rounded-md bg-logo-purple/85 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-logo-purple/70 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:ring-logo-purple/70"
                disabled={bMessage !== "Sign In"}
              >
                {bMessage}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}