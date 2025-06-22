#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, Env, String, Error, Symbol, 
    // New imports for the fixes:
    contracterror, symbol_short, 
};

// Define the product data structure
#[contracttype]
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Product {
    pub product_id: String,
    pub manufacturer: Address,
    pub current_owner: Address,
    pub registered_at: u64,
}

// Define storage key
#[contracttype]
pub enum DataKey {
    Product(String), // Use the product_id as part of the key for each product
}

// Define error codes
#[contracterror] // This attribute is crucial for the host to recognize these errors
#[derive(Copy, Clone, Debug, Eq, PartialEq, PartialOrd, Ord)] // Add Copy derive
#[repr(u32)]
pub enum ContractError {
    ProductAlreadyExists = 100,
    ProductNotFound = 101,
    NotAuthorized = 102,
}

// Define event topics
const REGISTER: Symbol = symbol_short!("REGISTR"); // Use symbol_short! macro
const TRANSFER: Symbol = symbol_short!("TRANSFR"); // Use symbol_short! macro

#[contract]
pub struct ProductAuthenticityContract;

#[contractimpl]
impl ProductAuthenticityContract {
    /// Registers a new product, with the caller as the manufacturer and initial owner.
    /// The manufacturer's address must authorize this call.
    pub fn register_product(env: Env, manufacturer: Address, product_id: String) -> Result<String, Error> {
        // Ensure the manufacturer authorizes this transaction
        manufacturer.require_auth();

        // Create storage key for this product
        let key = DataKey::Product(product_id.clone());
        
        // Check if product already exists in persistent storage
        if env.storage().persistent().has(&key) {
            // Corrected error handling: return the enum variant, which converts to Error
            return Err(ContractError::ProductAlreadyExists.into()); 
        }

        // Create new product
        let product = Product {
            product_id: product_id.clone(),
            manufacturer: manufacturer.clone(),
            current_owner: manufacturer.clone(),
            registered_at: env.ledger().timestamp(),
        };

        // Store the product in persistent storage
        env.storage().persistent().set(&key, &product);
        // Extend the TTL for this product entry. Adjust values as needed.
        // E.g., 50 ledgers (5 minutes approx) minimum for live, 100 ledgers (10 minutes approx) for max extension.
        env.storage().persistent().extend_ttl(&key, 50, 100);

        // Publish registration event - Corrected: use env.events().publish
        env.events().publish(
            (REGISTER, product_id.clone()), // Topics are often a tuple of Symbols and/or other Vals
            (manufacturer.clone(), product.registered_at), // Data can be a tuple of Vals
        );

        Ok(String::from_str(&env, "Product registered successfully"))
    }

    /// Retrieves details for a given product ID.
    pub fn get_product_details(env: Env, product_id: String) -> Result<Product, Error> {
        // Create storage key for this product
        let key = DataKey::Product(product_id.clone());
        
        // Try to get the product from persistent storage
        if let Some(product) = env.storage().persistent().get::<DataKey, Product>(&key) {
            Ok(product)
        } else {
            // Corrected error handling
            Err(ContractError::ProductNotFound.into())
        }
    }

    /// Transfers ownership of a product from the current owner to a new owner.
    /// The current owner's address must authorize this call.
    pub fn transfer_ownership(env: Env, current_owner: Address, product_id: String, new_owner: Address) -> Result<String, Error> {
        // Ensure the current owner authorizes this transaction
        current_owner.require_auth();

        // Create storage key for this product
        let key = DataKey::Product(product_id.clone());
        
        // Try to get the product from persistent storage
        if let Some(mut product) = env.storage().persistent().get::<DataKey, Product>(&key) {
            // Verify that the caller (current_owner) is indeed the product's current_owner
            if current_owner != product.current_owner {
                // Corrected error handling
                return Err(ContractError::NotAuthorized.into());
            }
            
            // Update the current owner
            let old_owner = product.current_owner.clone();
            product.current_owner = new_owner.clone();
            
            // Save the updated product back to persistent storage
            env.storage().persistent().set(&key, &product);
            // Extend TTL for the updated entry
            env.storage().persistent().extend_ttl(&key, 50, 100);

            // Publish transfer event - Corrected: use env.events().publish
            env.events().publish(
                (TRANSFER, product_id.clone()), // Topics
                (old_owner, new_owner.clone()), // Data
            );
            
            Ok(String::from_str(&env, "Ownership transferred successfully"))
        } else {
            // Corrected error handling
            Err(ContractError::ProductNotFound.into())
        }
    }
}

mod test;