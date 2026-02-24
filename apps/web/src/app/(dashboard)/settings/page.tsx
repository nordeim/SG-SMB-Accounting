import { Metadata } from "next";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Settings, Building, User, Bell, Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Settings — LedgerSG",
  description: "Manage your account and organization settings",
};

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-primary">
            Settings
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage your account and organization
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {/* Organization Settings */}
        <Card className="border-border bg-carbon rounded-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Building className="h-5 w-5 text-accent-primary" />
              <CardTitle className="font-display text-lg text-text-primary">
                Organization
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Input
                label="Company Name"
                defaultValue="Demo Company Pte Ltd"
              />
              <Input label="UEN" defaultValue="201912345A" />
              <Input label="GST Registration No" defaultValue="M90345678" />
              <Input
                label="Address"
                defaultValue="123 Business Street, Singapore"
              />
            </div>
            <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
              Save Changes
            </Button>
          </CardContent>
        </Card>

        {/* User Settings */}
        <Card className="border-border bg-carbon rounded-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-accent-primary" />
              <CardTitle className="font-display text-lg text-text-primary">
                User Profile
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <Input label="Full Name" defaultValue="Demo User" />
              <Input label="Email" defaultValue="demo@ledgersg.sg" />
              <Input label="Phone" defaultValue="+65 9123 4567" />
            </div>
            <Button className="rounded-sm bg-accent-primary text-void hover:bg-accent-primary-dim">
              Update Profile
            </Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="border-border bg-carbon rounded-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Bell className="h-5 w-5 text-accent-primary" />
              <CardTitle className="font-display text-lg text-text-primary">
                Notifications
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-secondary">
              Notification settings will be available in a future update.
            </p>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card className="border-border bg-carbon rounded-sm">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-accent-primary" />
              <CardTitle className="font-display text-lg text-text-primary">
                Security
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button
              variant="outline"
              className="rounded-sm border-border text-text-secondary"
            >
              Change Password
            </Button>
            <Button
              variant="outline"
              className="rounded-sm border-border text-text-secondary ml-2"
            >
              Enable 2FA
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
