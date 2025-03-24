# Angular Frontend Implementation Guide for Financial Entities

This guide outlines how to implement CRUD operations for all financial entities related to case persons in the Angular frontend application. This includes bank accounts, credit cards, loans, assets, and other financial entities.

## Financial Entities Overview

Based on the backend structure, the following financial entities should be implemented:

1. Bank Accounts
2. Credit Cards
3. Loans
4. Assets
5. Income Sources

## Common Implementation Patterns

All financial entities follow a similar pattern with slight variations in data models.

### Directory Structure

```
src/
  app/
    models/
      bank-account.model.ts
      credit-card.model.ts
      loan.model.ts
      asset.model.ts
      income-source.model.ts
    services/
      bank-account.service.ts
      credit-card.service.ts
      loan.service.ts
      asset.service.ts
      income-source.service.ts
    components/
      financial-entities/
        bank-accounts/
          bank-account-list.component.ts
          bank-account-form.component.ts
        credit-cards/
          credit-card-list.component.ts
          credit-card-form.component.ts
        loans/
          loan-list.component.ts
          loan-form.component.ts
        assets/
          asset-list.component.ts
          asset-form.component.ts
        income-sources/
          income-source-list.component.ts
          income-source-form.component.ts
```

## Data Models Implementation

### 1. Bank Account Model

```typescript
// src/app/models/bank-account.model.ts

export interface BankAccount {
  id: string;
  person_id: string;
  bank_id: string;
  account_number: string;
  account_type_id: string;
  branch: string;
  created_at: string;
  updated_at: string;
}

export interface BankAccountCreate {
  person_id: string;
  bank_id: string;
  account_number: string;
  account_type_id: string;
  branch: string;
}

export interface BankAccountUpdate {
  bank_id?: string;
  account_number?: string;
  account_type_id?: string;
  branch?: string;
}
```

### 2. Credit Card Model

```typescript
// src/app/models/credit-card.model.ts

export interface CreditCard {
  id: string;
  person_id: string;
  credit_card_type_id: string;
  card_number: string; // Last 4 digits typically
  expiry_date: string;
  credit_limit: number;
  created_at: string;
  updated_at: string;
}

export interface CreditCardCreate {
  person_id: string;
  credit_card_type_id: string;
  card_number: string;
  expiry_date: string;
  credit_limit: number;
}

export interface CreditCardUpdate {
  credit_card_type_id?: string;
  card_number?: string;
  expiry_date?: string;
  credit_limit?: number;
}
```

### 3. Loan Model

```typescript
// src/app/models/loan.model.ts

export interface Loan {
  id: string;
  person_id: string;
  loan_type_id: string;
  loan_goal_id: string;
  financial_org_id: string;
  amount: number;
  monthly_payment: number;
  interest_rate: number;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
}

export interface LoanCreate {
  person_id: string;
  loan_type_id: string;
  loan_goal_id: string;
  financial_org_id: string;
  amount: number;
  monthly_payment: number;
  interest_rate: number;
  start_date: string;
  end_date: string;
}

export interface LoanUpdate {
  loan_type_id?: string;
  loan_goal_id?: string;
  financial_org_id?: string;
  amount?: number;
  monthly_payment?: number;
  interest_rate?: number;
  start_date?: string;
  end_date?: string;
}
```

### 4. Asset Model

```typescript
// src/app/models/asset.model.ts

export interface Asset {
  id: string;
  person_id: string;
  asset_type_id: string;
  label: string;
  value: number;
  description?: string;
  address?: string;
  created_at: string;
  updated_at: string;
}

export interface AssetCreate {
  person_id: string;
  asset_type_id: string;
  label: string;
  value: number;
  description?: string;
  address?: string;
}

export interface AssetUpdate {
  asset_type_id?: string;
  label?: string;
  value?: number;
  description?: string;
  address?: string;
}
```

### 5. Income Source Model

```typescript
// src/app/models/income-source.model.ts

export interface IncomeSource {
  id: string;
  person_id: string;
  income_source_type_id: string;
  monthly_income: number;
  description: string;
  employment_id?: string; // Only for employment income
  created_at: string;
  updated_at: string;
}

export interface IncomeSourceCreate {
  person_id: string;
  income_source_type_id: string;
  monthly_income: number;
  description: string;
  employment_id?: string;
}

export interface IncomeSourceUpdate {
  income_source_type_id?: string;
  monthly_income?: number;
  description?: string;
  employment_id?: string;
}
```

## Services Implementation

Each financial entity will need a service to handle API calls. Here's the pattern for each:

### 1. Bank Account Service

```typescript
// src/app/services/bank-account.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { BankAccount, BankAccountCreate, BankAccountUpdate } from '../models/bank-account.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BankAccountService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get all bank accounts for a person
  getBankAccounts(personId: string): Observable<BankAccount[]> {
    return this.http.get<BankAccount[]>(`${this.apiUrl}/persons/${personId}/bank-accounts`);
  }

  // Get a specific bank account
  getBankAccount(personId: string, accountId: string): Observable<BankAccount> {
    return this.http.get<BankAccount>(`${this.apiUrl}/persons/${personId}/bank-accounts/${accountId}`);
  }

  // Create a new bank account
  createBankAccount(account: BankAccountCreate): Observable<BankAccount> {
    return this.http.post<BankAccount>(`${this.apiUrl}/persons/${account.person_id}/bank-accounts`, account);
  }

  // Update a bank account
  updateBankAccount(personId: string, accountId: string, account: BankAccountUpdate): Observable<BankAccount> {
    return this.http.put<BankAccount>(`${this.apiUrl}/persons/${personId}/bank-accounts/${accountId}`, account);
  }

  // Delete a bank account
  deleteBankAccount(personId: string, accountId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/persons/${personId}/bank-accounts/${accountId}`);
  }
}
```

### 2. Credit Card Service

```typescript
// src/app/services/credit-card.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { CreditCard, CreditCardCreate, CreditCardUpdate } from '../models/credit-card.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class CreditCardService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get all credit cards for a person
  getCreditCards(personId: string): Observable<CreditCard[]> {
    return this.http.get<CreditCard[]>(`${this.apiUrl}/persons/${personId}/credit-cards`);
  }

  // Get a specific credit card
  getCreditCard(personId: string, cardId: string): Observable<CreditCard> {
    return this.http.get<CreditCard>(`${this.apiUrl}/persons/${personId}/credit-cards/${cardId}`);
  }

  // Create a new credit card
  createCreditCard(card: CreditCardCreate): Observable<CreditCard> {
    return this.http.post<CreditCard>(`${this.apiUrl}/persons/${card.person_id}/credit-cards`, card);
  }

  // Update a credit card
  updateCreditCard(personId: string, cardId: string, card: CreditCardUpdate): Observable<CreditCard> {
    return this.http.put<CreditCard>(`${this.apiUrl}/persons/${personId}/credit-cards/${cardId}`, card);
  }

  // Delete a credit card
  deleteCreditCard(personId: string, cardId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/persons/${personId}/credit-cards/${cardId}`);
  }
}
```

### 3. Loan Service

```typescript
// src/app/services/loan.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Loan, LoanCreate, LoanUpdate } from '../models/loan.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class LoanService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get all loans for a person
  getLoans(personId: string): Observable<Loan[]> {
    return this.http.get<Loan[]>(`${this.apiUrl}/persons/${personId}/loans`);
  }

  // Get a specific loan
  getLoan(personId: string, loanId: string): Observable<Loan> {
    return this.http.get<Loan>(`${this.apiUrl}/persons/${personId}/loans/${loanId}`);
  }

  // Create a new loan
  createLoan(loan: LoanCreate): Observable<Loan> {
    return this.http.post<Loan>(`${this.apiUrl}/persons/${loan.person_id}/loans`, loan);
  }

  // Update a loan
  updateLoan(personId: string, loanId: string, loan: LoanUpdate): Observable<Loan> {
    return this.http.put<Loan>(`${this.apiUrl}/persons/${personId}/loans/${loanId}`, loan);
  }

  // Delete a loan
  deleteLoan(personId: string, loanId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/persons/${personId}/loans/${loanId}`);
  }
}
```

### 4. Asset Service

```typescript
// src/app/services/asset.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Asset, AssetCreate, AssetUpdate } from '../models/asset.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class AssetService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get all assets for a person
  getAssets(personId: string): Observable<Asset[]> {
    return this.http.get<Asset[]>(`${this.apiUrl}/persons/${personId}/assets`);
  }

  // Get a specific asset
  getAsset(personId: string, assetId: string): Observable<Asset> {
    return this.http.get<Asset>(`${this.apiUrl}/persons/${personId}/assets/${assetId}`);
  }

  // Create a new asset
  createAsset(asset: AssetCreate): Observable<Asset> {
    return this.http.post<Asset>(`${this.apiUrl}/persons/${asset.person_id}/assets`, asset);
  }

  // Update an asset
  updateAsset(personId: string, assetId: string, asset: AssetUpdate): Observable<Asset> {
    return this.http.put<Asset>(`${this.apiUrl}/persons/${personId}/assets/${assetId}`, asset);
  }

  // Delete an asset
  deleteAsset(personId: string, assetId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/persons/${personId}/assets/${assetId}`);
  }
}
```

### 5. Income Source Service

```typescript
// src/app/services/income-source.service.ts

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { IncomeSource, IncomeSourceCreate, IncomeSourceUpdate } from '../models/income-source.model';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class IncomeSourceService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) { }

  // Get all income sources for a person
  getIncomeSources(personId: string): Observable<IncomeSource[]> {
    return this.http.get<IncomeSource[]>(`${this.apiUrl}/persons/${personId}/income-sources`);
  }

  // Get a specific income source
  getIncomeSource(personId: string, sourceId: string): Observable<IncomeSource> {
    return this.http.get<IncomeSource>(`${this.apiUrl}/persons/${personId}/income-sources/${sourceId}`);
  }

  // Create a new income source
  createIncomeSource(source: IncomeSourceCreate): Observable<IncomeSource> {
    return this.http.post<IncomeSource>(`${this.apiUrl}/persons/${source.person_id}/income-sources`, source);
  }

  // Update an income source
  updateIncomeSource(personId: string, sourceId: string, source: IncomeSourceUpdate): Observable<IncomeSource> {
    return this.http.put<IncomeSource>(`${this.apiUrl}/persons/${personId}/income-sources/${sourceId}`, source);
  }

  // Delete an income source
  deleteIncomeSource(personId: string, sourceId: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/persons/${personId}/income-sources/${sourceId}`);
  }
}
```

## Component Implementation

For each financial entity, you'll need two components:
1. List component - to display all entities of a type
2. Form component - to add/edit entities

Here's an example pattern for Bank Accounts that can be adapted for other entities:

### List Component (Bank Accounts)

```typescript
// src/app/components/financial-entities/bank-accounts/bank-account-list.component.ts

import { Component, Input, OnInit } from '@angular/core';
import { BankAccountService } from '../../../services/bank-account.service';
import { BankAccount } from '../../../models/bank-account.model';
import { MatDialog } from '@angular/material/dialog';
import { BankAccountFormComponent } from './bank-account-form.component';
import { FinOrgService } from '../../../services/fin-org.service';

@Component({
  selector: 'app-bank-account-list',
  templateUrl: './bank-account-list.component.html',
  styleUrls: ['./bank-account-list.component.scss']
})
export class BankAccountListComponent implements OnInit {
  @Input() personId: string;
  accounts: BankAccount[] = [];
  displayedColumns: string[] = ['bank', 'accountNumber', 'branch', 'accountType', 'actions'];
  isLoading = false;
  banks: any[] = [];

  constructor(
    private accountService: BankAccountService,
    private finOrgService: FinOrgService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.loadAccounts();
    this.loadBanks();
  }

  loadAccounts(): void {
    this.isLoading = true;
    this.accountService.getBankAccounts(this.personId)
      .subscribe({
        next: (accounts) => {
          this.accounts = accounts;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading bank accounts:', error);
          this.isLoading = false;
        }
      });
  }

  loadBanks(): void {
    this.finOrgService.getBanks().subscribe(banks => {
      this.banks = banks;
    });
  }

  getBankName(bankId: string): string {
    const bank = this.banks.find(b => b.id === bankId);
    return bank ? bank.name : bankId;
  }

  openAccountForm(account?: BankAccount): void {
    const dialogRef = this.dialog.open(BankAccountFormComponent, {
      width: '500px',
      data: { 
        personId: this.personId,
        account: account
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadAccounts();
      }
    });
  }

  deleteAccount(account: BankAccount): void {
    if (confirm(`Are you sure you want to delete this bank account?`)) {
      this.accountService.deleteBankAccount(this.personId, account.id)
        .subscribe({
          next: () => {
            this.loadAccounts();
          },
          error: (error) => {
            console.error('Error deleting bank account:', error);
          }
        });
    }
  }
}
```

### List Component Template (Bank Accounts)

```html
<!-- src/app/components/financial-entities/bank-accounts/bank-account-list.component.html -->

<div class="bank-accounts-container">
  <div class="header-actions">
    <h2>Bank Accounts</h2>
    <button mat-raised-button color="primary" (click)="openAccountForm()">
      <mat-icon>add</mat-icon> Add Bank Account
    </button>
  </div>

  <mat-progress-bar *ngIf="isLoading" mode="indeterminate"></mat-progress-bar>

  <div *ngIf="!isLoading && accounts.length === 0" class="no-data">
    No bank accounts found for this person.
  </div>

  <table mat-table [dataSource]="accounts" class="mat-elevation-z2" *ngIf="accounts.length > 0">
    <!-- Bank Column -->
    <ng-container matColumnDef="bank">
      <th mat-header-cell *matHeaderCellDef>Bank</th>
      <td mat-cell *matCellDef="let account">{{ getBankName(account.bank_id) }}</td>
    </ng-container>

    <!-- Account Number Column -->
    <ng-container matColumnDef="accountNumber">
      <th mat-header-cell *matHeaderCellDef>Account Number</th>
      <td mat-cell *matCellDef="let account">{{ account.account_number }}</td>
    </ng-container>

    <!-- Branch Column -->
    <ng-container matColumnDef="branch">
      <th mat-header-cell *matHeaderCellDef>Branch</th>
      <td mat-cell *matCellDef="let account">{{ account.branch }}</td>
    </ng-container>

    <!-- Account Type Column -->
    <ng-container matColumnDef="accountType">
      <th mat-header-cell *matHeaderCellDef>Account Type</th>
      <td mat-cell *matCellDef="let account">
        <!-- You'll need to implement a pipe or service to convert account_type_id to a readable name -->
        {{ account.account_type_id }}
      </td>
    </ng-container>

    <!-- Actions Column -->
    <ng-container matColumnDef="actions">
      <th mat-header-cell *matHeaderCellDef>Actions</th>
      <td mat-cell *matCellDef="let account">
        <button mat-icon-button color="primary" (click)="openAccountForm(account)">
          <mat-icon>edit</mat-icon>
        </button>
        <button mat-icon-button color="warn" (click)="deleteAccount(account)">
          <mat-icon>delete</mat-icon>
        </button>
      </td>
    </ng-container>

    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
  </table>
</div>
```

### Form Component (Bank Accounts)

```typescript
// src/app/components/financial-entities/bank-accounts/bank-account-form.component.ts

import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { BankAccountService } from '../../../services/bank-account.service';
import { BankAccount } from '../../../models/bank-account.model';
import { FinOrgService } from '../../../services/fin-org.service';
import { BankAccountTypeService } from '../../../services/bank-account-type.service';

@Component({
  selector: 'app-bank-account-form',
  templateUrl: './bank-account-form.component.html',
  styleUrls: ['./bank-account-form.component.scss']
})
export class BankAccountFormComponent implements OnInit {
  accountForm: FormGroup;
  isEditMode: boolean;
  banks: any[] = [];
  accountTypes: any[] = [];
  isSubmitting = false;

  constructor(
    private fb: FormBuilder,
    private accountService: BankAccountService,
    private finOrgService: FinOrgService,
    private accountTypeService: BankAccountTypeService,
    private dialogRef: MatDialogRef<BankAccountFormComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { personId: string, account?: BankAccount }
  ) {
    this.isEditMode = !!data.account;
    this.accountForm = this.fb.group({
      bank_id: [data.account?.bank_id || '', Validators.required],
      account_number: [data.account?.account_number || '', Validators.required],
      branch: [data.account?.branch || '', Validators.required],
      account_type_id: [data.account?.account_type_id || '', Validators.required]
    });
  }

  ngOnInit(): void {
    this.loadBanks();
    this.loadAccountTypes();
  }

  loadBanks(): void {
    this.finOrgService.getBanks().subscribe(banks => {
      this.banks = banks;
    });
  }

  loadAccountTypes(): void {
    this.accountTypeService.getAccountTypes().subscribe(types => {
      this.accountTypes = types;
    });
  }

  onSubmit(): void {
    if (this.accountForm.invalid) {
      return;
    }

    this.isSubmitting = true;

    if (this.isEditMode) {
      this.accountService.updateBankAccount(
        this.data.personId,
        this.data.account!.id,
        this.accountForm.value
      ).subscribe({
        next: (result) => {
          this.isSubmitting = false;
          this.dialogRef.close(result);
        },
        error: (error) => {
          console.error('Error updating bank account:', error);
          this.isSubmitting = false;
        }
      });
    } else {
      const newAccount = {
        ...this.accountForm.value,
        person_id: this.data.personId
      };

      this.accountService.createBankAccount(newAccount).subscribe({
        next: (result) => {
          this.isSubmitting = false;
          this.dialogRef.close(result);
        },
        error: (error) => {
          console.error('Error creating bank account:', error);
          this.isSubmitting = false;
        }
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close();
  }
}
```

### Form Component Template (Bank Accounts)

```html
<!-- src/app/components/financial-entities/bank-accounts/bank-account-form.component.html -->

<h2 mat-dialog-title>{{ isEditMode ? 'Edit' : 'Add' }} Bank Account</h2>

<form [formGroup]="accountForm" (ngSubmit)="onSubmit()">
  <mat-dialog-content>
    <div class="form-field-container">
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Bank</mat-label>
        <mat-select formControlName="bank_id" required>
          <mat-option *ngFor="let bank of banks" [value]="bank.id">
            {{ bank.name }}
          </mat-option>
        </mat-select>
        <mat-error *ngIf="accountForm.get('bank_id')?.hasError('required')">
          Bank is required
        </mat-error>
      </mat-form-field>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Account Number</mat-label>
        <input matInput formControlName="account_number" required>
        <mat-error *ngIf="accountForm.get('account_number')?.hasError('required')">
          Account number is required
        </mat-error>
      </mat-form-field>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Branch</mat-label>
        <input matInput formControlName="branch" required>
        <mat-error *ngIf="accountForm.get('branch')?.hasError('required')">
          Branch is required
        </mat-error>
      </mat-form-field>

      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Account Type</mat-label>
        <mat-select formControlName="account_type_id" required>
          <mat-option *ngFor="let type of accountTypes" [value]="type.id">
            {{ type.name }}
          </mat-option>
        </mat-select>
        <mat-error *ngIf="accountForm.get('account_type_id')?.hasError('required')">
          Account type is required
        </mat-error>
      </mat-form-field>
    </div>
  </mat-dialog-content>

  <mat-dialog-actions align="end">
    <button mat-button type="button" [disabled]="isSubmitting" (click)="onCancel()">Cancel</button>
    <button mat-raised-button color="primary" type="submit" [disabled]="accountForm.invalid || isSubmitting">
      {{ isSubmitting ? 'Saving...' : (isEditMode ? 'Update' : 'Create') }}
    </button>
  </mat-dialog-actions>
</form>
```

## Financial Entities Tab Component

Create a parent component to organize all financial entities for a person:

```typescript
// src/app/components/financial-entities/financial-entities-tab.component.ts

import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-financial-entities-tab',
  templateUrl: './financial-entities-tab.component.html',
  styleUrls: ['./financial-entities-tab.component.scss']
})
export class FinancialEntitiesTabComponent {
  @Input() personId: string;
}
```

```html
<!-- src/app/components/financial-entities/financial-entities-tab.component.html -->

<div class="financial-entities-container">
  <mat-tab-group>
    <mat-tab label="Bank Accounts">
      <app-bank-account-list [personId]="personId"></app-bank-account-list>
    </mat-tab>
    <mat-tab label="Credit Cards">
      <app-credit-card-list [personId]="personId"></app-credit-card-list>
    </mat-tab>
    <mat-tab label="Loans">
      <app-loan-list [personId]="personId"></app-loan-list>
    </mat-tab>
    <mat-tab label="Assets">
      <app-asset-list [personId]="personId"></app-asset-list>
    </mat-tab>
    <mat-tab label="Income Sources">
      <app-income-source-list [personId]="personId"></app-income-source-list>
    </mat-tab>
  </mat-tab-group>
</div>
```

## Common Styling

Create a common SCSS file for financial entities:

```scss
/* src/app/components/financial-entities/financial-entities.scss */

.financial-entity-container {
  padding: 20px;
  
  .header-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .no-data {
    text-align: center;
    padding: 20px;
    background-color: #f5f5f5;
    border-radius: 4px;
    margin-top: 20px;
  }
  
  table {
    width: 100%;
  }
}

.form-field-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  
  .full-width {
    width: 100%;
  }
}

.mat-tab-group {
  margin-top: 20px;
}
```

## Error Handling Service

Implement a common error handling service:

```typescript
// src/app/services/error.service.ts

import { Injectable } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';

@Injectable({
  providedIn: 'root'
})
export class ErrorService {
  constructor(private snackBar: MatSnackBar) {}

  showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  handleApiError(error: any, entityType: string): void {
    let errorMessage = `Failed to process ${entityType}.`;
    
    if (error.status === 404) {
      errorMessage = `${entityType} not found.`;
    } else if (error.status === 403) {
      errorMessage = `You don't have permission to access this ${entityType}.`;
    } else if (error.status === 400) {
      errorMessage = `Invalid data for ${entityType}.`;
    }
    
    this.showError(errorMessage);
    console.error(`${entityType} error:`, error);
  }
}
```

## Module Registration

Register all components in the appropriate Angular module:

```typescript
// src/app/financial-entities/financial-entities.module.ts

import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDialogModule } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

import { BankAccountListComponent } from './bank-accounts/bank-account-list.component';
import { BankAccountFormComponent } from './bank-accounts/bank-account-form.component';
import { CreditCardListComponent } from './credit-cards/credit-card-list.component';
import { CreditCardFormComponent } from './credit-cards/credit-card-form.component';
import { LoanListComponent } from './loans/loan-list.component';
import { LoanFormComponent } from './loans/loan-form.component';
import { AssetListComponent } from './assets/asset-list.component';
import { AssetFormComponent } from './assets/asset-form.component';
import { IncomeSourceListComponent } from './income-sources/income-source-list.component';
import { IncomeSourceFormComponent } from './income-sources/income-source-form.component';
import { FinancialEntitiesTabComponent } from './financial-entities-tab.component';

@NgModule({
  declarations: [
    BankAccountListComponent,
    BankAccountFormComponent,
    CreditCardListComponent,
    CreditCardFormComponent,
    LoanListComponent,
    LoanFormComponent,
    AssetListComponent,
    AssetFormComponent,
    IncomeSourceListComponent,
    IncomeSourceFormComponent,
    FinancialEntitiesTabComponent
  ],
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDialogModule,
    MatProgressBarModule,
    MatTabsModule,
    MatDatepickerModule,
    MatNativeDateModule
  ],
  exports: [
    FinancialEntitiesTabComponent
  ]
})
export class FinancialEntitiesModule {}
```

## Integration with Person Details

Include the financial entities tab in the person details component:

```html
<!-- src/app/components/person/person-details.component.html -->

<mat-tab-group>
  <mat-tab label="Basic Info">
    <!-- Basic person information -->
  </mat-tab>
  <mat-tab label="Financial Entities">
    <app-financial-entities-tab [personId]="personId"></app-financial-entities-tab>
  </mat-tab>
  <!-- Other tabs like Documents, etc. -->
</mat-tab-group>
```

## Testing Strategy

For each financial entity, you should create:

1. Unit tests for services
2. Component tests for the list and form components
3. Integration tests for the overall financial entities tab

Here's an example for the Bank Account service:

```typescript
// src/app/services/bank-account.service.spec.ts

import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { BankAccountService } from './bank-account.service';
import { environment } from '../../environments/environment';

describe('BankAccountService', () => {
  let service: BankAccountService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [BankAccountService]
    });
    
    service = TestBed.inject(BankAccountService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should get bank accounts for a person', () => {
    const mockAccounts = [
      { id: '1', person_id: '123', bank_id: 'bank1', account_number: '12345', account_type_id: 'type1', branch: '001', created_at: '', updated_at: '' }
    ];
    const personId = '123';

    service.getBankAccounts(personId).subscribe(accounts => {
      expect(accounts).toEqual(mockAccounts);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/persons/${personId}/bank-accounts`);
    expect(req.request.method).toBe('GET');
    req.flush(mockAccounts);
  });

  // Add more tests for other methods
});
```

## Conclusion

This comprehensive guide provides the foundation for implementing CRUD operations for all financial entities related to case persons in your Angular application. The implementations follow consistent patterns, making it easier to maintain and extend the codebase as needed.

Remember to:
1. Create data models for each entity
2. Implement services for API communication
3. Create list components for displaying entities
4. Create form components for adding/editing entities
5. Organize everything within the financial entities tab
6. Test thoroughly

By following this guide, you'll have a complete and consistent implementation for managing financial entities in your Angular application.