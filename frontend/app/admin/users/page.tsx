"use client";

import React, { useEffect, useState } from "react";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

// Mock user data (replace with API call)
const MOCK_USERS = [
  { id: "1", name: "อ.สมชาย ใจดี", email: "somchai@univ.ac.th", role: "admin", status: "active" },
  { id: "2", name: "อ.วิไลวรรณ สอนดี", email: "wilai@univ.ac.th", role: "teacher", status: "active" },
  { id: "3", name: "อ.ประเสริฐ เก่งมาก", email: "prasert@univ.ac.th", role: "teacher", status: "inactive" },
];

export default function AdminUsersPage() {
  const [users, setUsers] = useState(MOCK_USERS);
  // TODO: Replace with real API fetch

  return (
    <ProtectedRoute requiredRole="admin">
      <div className="max-w-4xl mx-auto py-10">
        <h1 className="text-2xl font-bold mb-6">User Management</h1>
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-5 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
            <h2 className="text-lg font-bold text-slate-800">Users</h2>
            <Button variant="default" className="rounded-lg">Add User</Button>
          </div>
          <div className="p-2">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      <Badge variant={user.role === "admin" ? "default" : "secondary"}>
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.status === "active" ? "default" : "secondary"}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button size="sm" variant="outline" className="mr-2">Edit</Button>
                      <Button size="sm" variant="destructive">Delete</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
